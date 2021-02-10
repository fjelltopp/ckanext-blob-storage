import ReactDOM from 'react-dom';
import React, { useState } from 'react';
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

  // fetch authToken from ckan authz_authorize
  if (!authToken) {
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

  // return file input form
  if (uploadProgress.total == 0) {
    const handleClick = async inputFiles => {
      if (!inputFiles[0]) return;
      const file = open(inputFiles[0]);
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
    return (
      <div className="image-upload">
        <div className="form-group control-full">
          <label className="control-label" htmlFor="field-image-upload">File</label>
          <div className="controls">
            <input
              id="field-image-upload"
              type="file"
              className="form-control"
              title="Upload a file on your computer"
              style={{ width: 90 }}
              onChange={e => handleClick(e.target.files)}
            />
            <a className="btn btn-default"><i className="fa fa-cloud-upload"></i>Upload</a>
          </div>
        </div>
      </div>
    )
  }

  // return progress bar
  const progressBar = () => {
    const percent = Math.round(
      (uploadProgress.loaded / uploadProgress.total) * 100
    );
    return percent < 100 || !hiddenInputs.name
      ? (
        <div className="form-group controls progress progress-striped active">
          <div
            className="progress-bar"
            style={{ width: `${percent}%` }}
          >
            <span>{percent}%</span>
          </div>
        </div>
      )
      : (
        <div className="form-group controls progress">
          <div
            className="progress-bar progress-bar-success"
            style={{ width: `${percent}%` }}
          >
            <span><i className="fa fa-file"></i>&nbsp;{hiddenInputs.name}</span>
          </div>
        </div>
      )
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
      {progressBar()}
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
