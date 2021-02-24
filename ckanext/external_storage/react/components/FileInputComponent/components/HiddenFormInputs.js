import React from 'react';

export default function HiddenFormInputs({ hiddenInputs }) {

    // TODO: remove below logging
    console.log('----------------')
    Object.keys(hiddenInputs).forEach(key => {
        console.log(key, '=', hiddenInputs[key])
    });
    console.log('----------------')

    return Object.keys(hiddenInputs).map(key => (
        <input
            key={key}
            name={key}
            value={hiddenInputs[key] || ''}
            type="hidden"
        />
    ));

}