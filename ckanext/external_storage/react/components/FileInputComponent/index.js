import ReactDOM from 'react-dom';
import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone'
import { Client } from "giftless-client";
import axios from "axios";

function App({ lfsServer, orgId, datasetId, existingResourceData }) {
  const [authToken, setAuthToken] = useState();
  const [uploadType, setUploadType] = useState(null);
  const [urlValue, setUrlValue] = useState(null);
  const defaults = {
    uploadProgress: { loaded: 0, total: 0 },
    hiddenInputs: { sha256: null, name: null, size: null }
  }
  const [uploadProgress, setUploadProgress] =
    useState(defaults.uploadProgress);
  const [hiddenInputs, setHiddenInputs] =
    useState(defaults.hiddenInputs);
  const resetFileUploader = () => {
    setUploadProgress(defaults.uploadProgress);
    setHiddenInputs(defaults.hiddenInputs);
  }

  useEffect(() => {
    if (existingResourceData.urlType === 'upload') {
      // resource already has a file uploaded
      const data = existingResourceData;
      setUploadProgress({ loaded: data.size, total: data.size })
      setHiddenInputs({
        sha256: data.sha256, name: data.name, size: data.size
      })
    } else if (existingResourceData.url) {
      // resource already has a url set
      setUploadType('url');
      setUrlValue(existingResourceData.url);
    };
    axios.post(
      '/api/3/action/authz_authorize',
      { scopes: `obj:ckan/${datasetId}/*:write` },
      { withCredentials: true }
    )
      .then(res => {
        setAuthToken(res.data.result.token)
      })
      .catch(error => {
        console.log(`authz_authorize error: ${error}`);
        setAuthToken('error')
      })
  }, [setAuthToken, setUploadProgress, setHiddenInputs, setUploadType]);

  // return auth status if not completed
  if (!authToken) {
    return ckan.i18n._('Loading');
  } else if (authToken === 'error') {
    return ckan.i18n._('Authentication Error: Failed to load file uploader');
  }

  // return progress bar if file upload in progress
  if (uploadProgress.total) {
    const inputs = [
      { name: 'url_type', value: 'upload' },
      { name: 'lfs_prefix', value: [orgId, datasetId].join('/') },
      { name: 'url', value: hiddenInputs.name },
      { name: 'sha256', value: hiddenInputs.sha256 },
      { name: 'size', value: hiddenInputs.size }
    ];
    return (
      <>
        <ProgressBar
          {...{ uploadProgress, hiddenInputs, resetFileUploader }}
        />
        {inputs.map(input =>
          <input
            key={input.name}
            name={input.name}
            value={input.value || ''}
            type="hidden"
          />
        )}
      </>
    );
  }

  switch (uploadType) {
    default: {
      // return file uploader
      const handleFileSelected = async inputFile => {
        if (!inputFile) return;
        const file = data.open(inputFile);
        const client = new Client(lfsServer, authToken, ['basic']);
        await client.upload(file, orgId, datasetId, progress => {
          setUploadProgress({
            loaded: progress.loaded,
            total: progress.total
          });
        });
        setUploadProgress({ loaded: 100, total: 100 });
        setHiddenInputs({
          sha256: file._computedHashes.sha256,
          name: file._descriptor.name,
          size: file._descriptor.size,
        })
      }
      return <FileUploader {...{ handleFileSelected, setUploadType }} />
    }
    case 'url': {
      // return url field
      return (
        <div id="urlInputField">
          <label className="control-label" htmlFor="field-url">{ckan.i18n._('URL')}</label>
          <div className="input-group">
            <input
              key="url_type"
              name="url_type"
              value=""
              type="hidden"
            />
            <input
              id="field-url"
              type="url"
              name="url"
              placeholder="http://example.com/my-data.csv"
              className="form-control"
              defaultValue={urlValue}
            />
            <span className="input-group-btn">
              <button
                className="btn btn-danger"
                type="button"
                onClick={e => { setUploadType(null); e.preventDefault() }}
              >
                {ckan.i18n._('Remove')}
              </button>
            </span>
          </div>
        </div>
      );
    }
  }

}

function FileUploader({ handleFileSelected, setUploadType }) {
  const { getRootProps, getInputProps, open } = useDropzone({
    multiple: false,
    noClick: true,
    onDrop: acceptedFiles =>
      handleFileSelected(acceptedFiles[0]),
    onDropRejected: rejectedFiles =>
      handleFileSelected(rejectedFiles[0].file),
  })
  const uploadOptions = [
    {
      label: ckan.i18n._('Upload a file'),
      icon: 'fa-cloud-upload',
      onClick: e => {
        open(e);
        e.preventDefault();
      }
    },
    {
      label: ckan.i18n._('Link'),
      icon: 'fa-globe',
      onClick: e => {
        setUploadType('url');
        e.preventDefault();
      }
    }
  ]
  return (
    <div {...getRootProps({ className: 'dropzone' })}>
      <input {...getInputProps()} />
      <p>{ckan.i18n._('Drag a file into this box or')}</p>
      <div className="btn-group">
        {uploadOptions.map(option => (
          <button
            key={option.label}
            className="btn btn-default"
            onClick={option.onClick}
          >
            <i className={`fa ${option.icon}`}></i>
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function ProgressBar({ uploadProgress, hiddenInputs, resetFileUploader }) {
  const percent = Math.round(
    (uploadProgress.loaded / uploadProgress.total) * 100
  );
  const loaded = percent === 100 && hiddenInputs.name;
  return (
    <>
      {loaded
        ?
        <h3>
          <i className="fa fa-file"></i>
        &nbsp; {hiddenInputs.name} &nbsp;
        <i
            className="fa fa-close text-danger"
            style={{ cursor: 'pointer' }}
            title={ckan.i18n._('Remove')}
            onClick={resetFileUploader}
          ></i>
        </h3>
        :
        <div className={`form-group controls progress ${!loaded && 'progress-striped active'}`}>
          <div
            className="progress-bar"
            style={{ width: `${percent}%` }}
          >
            <span>{percent}%</span>
          </div>
        </div>
      }
    </>
  )
}

const componentElement =
  document.getElementById('FileInputComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const requiredString = str => {
  console.assert(str.length);
  return str;
}
const
  lfsServer = requiredString(getAttr('lfsServer')),
  orgId = requiredString(getAttr('orgId')),
  datasetId = requiredString(getAttr('datasetId'));

const existingResourceData = {
  urlType: getAttr('existingUrlType'),
  url: getAttr('existingUrl'),
  sha256: getAttr('existingSha256'),
  name: getAttr('existingName'),
  size: getAttr('existingSize'),
}

// wait for ckan.i18n to load
window.addEventListener('load', function () {
  ReactDOM.render(
    <App {...{
      lfsServer, orgId, datasetId,
      existingResourceData
    }} />,
    componentElement
  );
})
