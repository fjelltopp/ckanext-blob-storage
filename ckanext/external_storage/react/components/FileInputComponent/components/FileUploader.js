import React from 'react';
import { useDropzone } from 'react-dropzone'
import { Client } from "giftless-client";

export default function FileUploader({
    lfsServer, orgId, datasetId, authToken,
    setUploadProgress, setUploadFileName, setHiddenInputs
}) {

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
        setUploadFileName(file._descriptor.name);
        setHiddenInputs('file', {
            sha256: file._computedHashes.sha256,
            size: file._descriptor.size,
            url: file._descriptor.name
        })
    }

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
                setHiddenInputs('url', {});
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
