function updateClassroomData() {

    // Generate random people count
    let people = Math.floor(Math.random() * 21);


    // Determine occupancy level
    let occupancy;
    
    if (people === 0 || people <= 2) {
        occupancy = "LOW";
    } 
    else if (people <= 9) {
        occupancy = "MEDIUM";
    } 
    else {
        occupancy = "HIGH";
    }


    // Update occupancy display
    // Update occupancy display
    document.getElementById("people-count").textContent = people;
    document.getElementById("occupancy-level").textContent = occupancy;


    // Change occupancy panel color
    let occupancyPanel = document.getElementById("occupancy-panel");

    occupancyPanel.className = "card occupancy-panel " + occupancy.toLowerCase();
    

    // Generate current room temperature
    let currentTemperature = Math.floor(Math.random() * (32 - 24 + 1)) + 24;

    // Display current temperature
    document.getElementById("ac-temp").textContent = currentTemperature + "°C";


    // AC control
    let acIndicator = document.getElementById("ac-indicator");
    let acText = document.getElementById("ac-state-text");


    if (occupancy === "EMPTY" || occupancy === "LOW") {

        acIndicator.className = "ac-indicator off";
        acText.className = "ac-state-text off";

        acText.textContent = "OFF";

    } 

    else if (occupancy === "MEDIUM") {

        acIndicator.className = "ac-indicator on";
        acText.className = "ac-state-text on";

        acText.textContent = "ON (24°C)";

    } 

    else if (occupancy === "HIGH") {

        acIndicator.className = "ac-indicator on";
        acText.className = "ac-state-text on";

        acText.textContent = "ON (20°C)";
    }


    // Update last changed time
    document.getElementById("ac-last-changed").textContent =
        new Date().toLocaleTimeString();
}


// Run every 5 seconds
updateClassroomData();
setInterval(updateClassroomData, 5000);