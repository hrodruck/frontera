#!/usr/bin/env node

function updateZone(data, zoneName, newMessage, resetExplored = false) {
    // Create a deep copy to avoid modifying original data
    const updatedData = JSON.parse(JSON.stringify(data));
    
    // Update the zone message
    if (zoneName in updatedData.zones) {
        updatedData.zones[zoneName] = newMessage;
        
        // If reset_explored is true, set hasExplored to false for all users with this zone
        if (resetExplored) {
            for (const userId in updatedData.users) {
                if (updatedData.users[userId].zones && 
                    zoneName in updatedData.users[userId].zones) {
                    updatedData.users[userId].zones[zoneName].hasExplored = false;
                }
            }
        }
    }
    
    return updatedData;
}

// Main function
function main() {
    const fs = require('fs');

    // Check command line arguments
    const args = process.argv.slice(2);
    if (args.length !== 2) {
        console.error("Usage: node script.js <reset_explored: true/false> <path_to_updates_json>");
        process.exit(1);
    }

    const resetExploredStr = args[0].toLowerCase();
    const dataFilePath = 'data.json'; // Fixed input/output file
    const updatesFilePath = args[1]; // Assuming a separate updates file

    // Convert reset_explored to boolean
    if (resetExploredStr !== 'true' && resetExploredStr !== 'false') {
        console.error("Error: reset_explored must be 'true' or 'false'");
        process.exit(1);
    }
    const resetExplored = resetExploredStr === 'true';

    try {
        // Load original data from data.json
        let originalData;
        try {
            originalData = JSON.parse(fs.readFileSync(dataFilePath, 'utf8'));
        } catch (error) {
            console.error(`Error: Could not read ${dataFilePath}. Please ensure it exists and contains valid JSON`);
            process.exit(1);
        }

        // Read and parse the updates JSON file
        const updatesData = JSON.parse(fs.readFileSync(updatesFilePath, 'utf8'));

        // Validate updates data has 'zones'
        if (!updatesData.zones) {
            console.error("Error: Updates JSON must contain a 'zones' key");
            process.exit(1);
        }

        // Apply updates
        let updatedData = originalData;
        for (const [zoneName, newMessage] of Object.entries(updatesData.zones)) {
            updatedData = updateZone(updatedData, zoneName, newMessage, resetExplored);
        }

        // Save the updated data back to data.json
        fs.writeFileSync(dataFilePath, JSON.stringify(updatedData, null, 2));
        console.log("Updated data saved to data.json");
        console.log(JSON.stringify(updatedData, null, 2));

    } catch (error) {
        if (error.code === 'ENOENT') {
            console.error(`Error: File not found - ${error.path}`);
        } else if (error instanceof SyntaxError) {
            console.error("Error: Invalid JSON format in one of the input files");
        } else {
            console.error(`Error: An unexpected error occurred: ${error.message}`);
        }
        process.exit(1);
    }
}

// Run main function
main();