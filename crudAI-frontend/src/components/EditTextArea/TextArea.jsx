import React, { useState } from "react";
import "./TextArea.css";

const TextArea = ({ content, onCancel, onSubmit }) => {
    const [value, setValue] = useState(content)
  return (
    <div className="text-area-container">
      <div className="text-area-input-div">
        <input type="text" value={value} onChange={(e) => setValue(e.target.value)} />
      </div>
      <div className="text-area-buttons-div">
        <div>* Editing this message will make a new branch</div>
        <div className="text-area-buttons">
          <div className="cancel-button">
            <button onClick={onCancel}>Cancel</button>
          </div>
          <div className="submit-button">
            <button onClick={() => onSubmit(value)}>Submit</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextArea;
