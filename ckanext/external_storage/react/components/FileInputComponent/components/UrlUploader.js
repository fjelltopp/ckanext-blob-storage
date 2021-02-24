import React from 'react';

export default function UrlUploader({ linkUrl, resetComponent }) {

    return (
        <div id="urlInputField">
            <label className="control-label" htmlFor="field-url">
                {ckan.i18n._('URL')}
            </label>
            <div className="input-group">
                <input
                    id="field-url"
                    type="url"
                    name="url"
                    placeholder="http://example.com/my-data.csv"
                    className="form-control"
                    defaultValue={linkUrl}
                />
                <span className="input-group-btn">
                    <button
                        className="btn btn-danger"
                        type="button"
                        onClick={resetComponent}
                    >
                        {ckan.i18n._('Remove')}
                    </button>
                </span>
            </div>
        </div>
    );

}
