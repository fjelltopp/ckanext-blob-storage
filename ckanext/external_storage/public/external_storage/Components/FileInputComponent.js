import ReactDOM from 'react-dom';
import React, { useState } from 'react';
import { Client } from "giftless-client";
import { open } from "frictionless.js";
import axios from "axios";

const element = document.getElementById('FileInputComponent');
const getAttr = key => {
  const val = element.getAttribute(`data-${key}`);
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

function App() {
  const [authToken, setAuthToken] = useState();
  const [uploadProgress, setUploadProgress] = useState({
    loaded: 0, total: 0
  });
  const [hiddenInputs, setHiddenInputs] = useState({
    sha256: null, name: null, size: null
  })

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

  const lfsPrefix = [orgId, datasetId].join('/');
  const client = new Client(lfsServer, authToken, ['basic']);

  function onProgress(progress) {
    setUploadProgress({
      loaded: progress.loaded,
      total: progress.total
    });
  }

  const handleClick = async inputFiles => {
    if (!inputFiles[0]) return;
    const file = open(inputFiles[0]);
    await client.upload(file, orgId, datasetId, onProgress);
    setUploadProgress({ loaded: 100, total: 100 });
    setHiddenInputs({
      sha256: file._computedHashes.sha256,
      name: file._descriptor.name,
      size: file._descriptor.size,
    })
  }

  function uploadProgressPercent() {
    return Math.round(
      (uploadProgress.loaded / uploadProgress.total) * 100
    )
  }

  const inputs = [
    { name: 'url_type', value: 'upload' },
    { name: 'lfs_prefix', value: lfsPrefix },
    { name: 'url', value: hiddenInputs.name },
    { name: 'sha256', value: hiddenInputs.sha256 },
    { name: 'size', value: hiddenInputs.size }
  ];

  return (
    <>
      <input type="file" onChange={e => handleClick(e.target.files)} />
      {uploadProgress.total != 0 &&
        <>
          <p>{uploadProgressPercent()}% uploaded</p>
          {inputs.map(input =>
            <input
              key={input.name}
              name={input.name}
              value={input.value}
              type="hidden"
            />
          )}
        </>
      }
    </>
  );

}

ReactDOM.render(
  <App />,
  document.getElementById('FileInputComponent')
);