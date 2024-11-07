import axios from 'axios';
import React, { useState } from 'react';

// Service function to interact with the backend
export const generateFragrance = async (description: string): Promise<string> => {
    const response = await axios.post("http://localhost:5000/generate", { description });
    return response.data;
};

// FragranceGenerator component to handle input and display results
const FragranceGenerator: React.FC = () => {
    const [description, setDescription] = useState<string>(''); // State for description input
    const [fragrance, setFragrance] = useState<string>(''); // State for generated fragrance

    const handleGenerate = async () => {
        if (description.trim() === '') {
            return; // Prevent generating if description is empty
        }
        const result = await generateFragrance(description); // Call the generateFragrance function
        setFragrance(result); // Set the generated fragrance result
    };

    return (
        <div>
            <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)} // Update description state on input change
                placeholder="Enter fragrance description"
            />
            <button onClick={handleGenerate}>Generate Fragrance</button>
            {fragrance && <p>Generated Fragrance: {fragrance}</p>} {/* Display fragrance result */}
        </div>
    );
};

// Main App component
const App: React.FC = () => {
    return (
        <div>
            <h1>Fragrance Generator</h1>
            <FragranceGenerator /> {/* Render the FragranceGenerator component */}
        </div>
    );
};

export default App;
