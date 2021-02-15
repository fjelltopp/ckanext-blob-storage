import ReactDOM from 'react-dom';
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone'
import { Client } from "giftless-client";
import { open } from "frictionless.js";
import axios from "axios";

function App({ lfsServer, orgId, datasetId }) {
  const [authToken, setAuthToken] = useState();
  const [uploadProgress, setUploadProgress] = useState({
    loaded: 0, total: 0
  });
  const [hiddenInputs, setHiddenInputs] = useState({
    sha256: null, name: null, size: null
  })

  if (!authToken) {
    // fetch authToken from ckan authz_authorize
    axios.post(
      'http://adr/api/3/action/authz_authorize',
      { scopes: `obj:ckan/${datasetId}/*:write` },
      { withCredentials: true }
    )
      .then(res => setAuthToken(res.data.result.token))
      .catch(error => {
        console.log(`authz_authorize error: ${error}`);
        setAuthToken('error')
      })
    return 'Loading...';
  } else if (authToken === 'error') {
    return 'Authentication Error: Failed to load file uploader';
  }

  if (uploadProgress.total == 0) {
    const handleFileSelected = async inputFile => {
      if (!inputFile) return;
      const file = open(inputFile);
      const client = new Client(lfsServer, authToken, ['basic']);
      await client.upload(file, orgId, datasetId, onProgress);
      setUploadProgress({ loaded: 100, total: 100 });
      setHiddenInputs({
        sha256: file._computedHashes.sha256,
        name: file._descriptor.name,
        size: file._descriptor.size,
      })
    }
    function onProgress(progress) {
      setUploadProgress({
        loaded: progress.loaded,
        total: progress.total
      });
    }
    const fileUploader =
      <FileUploader handleFileSelected={handleFileSelected} />;
    return <Uploader fileUploader={fileUploader} />;
  }
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
        uploadProgress={uploadProgress}
        hiddenInputs={hiddenInputs}
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

function Uploader({ fileUploader }) {
  const [uploadType, setUploadType] = useState(null);
  switch (uploadType) {
    default: {
      // split screen between file uploader and url upload
      return (
        <div className="row">
          <div className="col-md-6">
            {fileUploader}
          </div>
          <div className="col-md-6">
            <div className="dropzone">
              <p>Add a linked resource</p>
              <button className="btn btn-default" onClick={() => setUploadType('url')}>
                <span><i className="fa fa-globe"></i> Link Resource</span>
              </button>
            </div>
          </div>
        </div>
      );
    }
    case 'url': {
      // replace both options with url upload
      return (
        <div className="form-group control-medium">
          <label className="control-label" htmlFor="field-url">URL</label>
          <div className="controls">
            <input
              id="field-url"
              type="url"
              name="url"
              placeholder="http://example.com/my-data.csv"
              className="form-control" />
          </div>
        </div>
      );
    }
  }
}

function FileUploader({ handleFileSelected }) {
  const { getRootProps, getInputProps } = useDropzone({
    multiple: false,
    onDrop: acceptedFiles =>
      handleFileSelected(acceptedFiles[0]),
    onDropRejected: rejectedFiles =>
      handleFileSelected(rejectedFiles[0].file),
  })
  return (
    <div {...getRootProps({ className: 'dropzone' })}>
      <input {...getInputProps()} />
      <p>Drag a file into this box or</p>
      <p className="btn btn-default">
        <span><i className="fa fa-cloud-upload"></i>Upload a file</span>
      </p>
    </div>
  )
}

function ProgressBar({ uploadProgress, hiddenInputs }) {
  const percent = Math.round(
    (uploadProgress.loaded / uploadProgress.total) * 100
  );
  const loaded = percent === 100 && hiddenInputs.name;
  return (
    <>
      {loaded && <p><i className="fa fa-file"></i>&nbsp;{hiddenInputs.name}</p>}
      <div className={`form-group controls progress ${!loaded && 'progress-striped active'}`}>
        <div
          className="progress-bar"
          style={{ width: `${percent}%` }}
        >
          <span>{percent}%</span>
        </div>
      </div>
    </>
  )
}

const componentElement =
  document.getElementById('FileInputComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return val in ['None', ''] ? null : val;
};
const requiredString = str => {
  console.assert(str.length);
  return str;
}
const
  lfsServer = requiredString(getAttr('lfsServer')),
  orgId = requiredString(getAttr('orgId')),
  datasetId = requiredString(getAttr('datasetId'));

ReactDOM.render(
  <App
    lfsServer={lfsServer}
    orgId={orgId}
    datasetId={datasetId}
  />,
  componentElement
);