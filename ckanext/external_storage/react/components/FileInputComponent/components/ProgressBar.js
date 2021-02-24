import React from 'react';

export default function ProgressBar({ uploadProgress }) {

    const percent = Math.round(
        (uploadProgress.loaded / uploadProgress.total) * 100
    );

    return (
        <div className="form-group controls progress progress-striped active">
            <div
                className="progress-bar"
                style={{ width: `${percent}%` }}
            >
                <span>{percent}%</span>
            </div>
        </div>
    )

}
