import React from 'react'
import './TextArea.css'

const TextArea = () => {
  return (
    <div className='text-area-container'>
        <div className="text-area-input-div">
            <input type='text' placeholder='hey'/>
        </div>
        <div className="text-area-buttons-div">
            <div>* Editing this message will make a new branch</div>
            <div className='text-area-buttons'>
                <div className="cancel-button">
                    <button>Cancel</button>
                </div>
                <div className="submit-button">
                    <button>Submit</button>
                </div>
            </div>
        </div>
      
    </div>
  )
}

export default TextArea
