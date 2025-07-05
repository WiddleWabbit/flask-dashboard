// Create a list of all the functions to be run to update reports
let reportDateCallbacks = [];

// Add a function to be run to update reports on date change, to the list.
function registerReportDateCallback(callback) {
    reportDateCallbacks.push(callback);
}

// Update all the reports
function updateReports() {
    // Run all the report call backs for the new dates
    reportDateCallbacks.forEach(callback => callback());
}

// A quick filter range was selected, update the dates and filter accordingly
function applyPredefinedRange() {
    const range = document.getElementById('rangeSelect').value;
    let startDate, endDate = dayjs();

    if (range === '5days') {
        startDate = dayjs();
        endDate = dayjs().add(5, 'day');
    } else if (range === '3days') {
        startDate = dayjs();
        endDate = dayjs().add(3, 'day');
    } else if (range === 'thisweek') {
        startDate = dayjs().startOf('week');
        endDate = dayjs().endOf('week');
    } else if (range === 'prev7days') {
        startDate = dayjs().subtract(7, 'day');
    } else if (range === 'prev30days') {
        startDate = dayjs().subtract(30, 'day');
    } else if (range === 'prev90days') {
        startDate = dayjs().subtract(90, 'day');
    } else {
        // Fetch all data
        document.getElementById('startdate').value = '';
        document.getElementById('enddate').value = '';
        updateReports();
        return;
    }

    // Format the dates
    document.getElementById('startdate').value = startDate.format('YYYY-MM-DD');
    document.getElementById('enddate').value = endDate.format('YYYY-MM-DD');
    // Now we have the dates formatted, run the updates
    updateReports();
    
}

// Add listeners to all report checkboxes, so that they toggle on click
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('#toggle-reports input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {

            // Get Variables for API Call to disable or enable in database
            const ID = this.value;
            const active = this.checked ? 1 : 0
            const reportId = `report-${this.value}`;
            const reportDiv = document.getElementById(reportId);

            // Build the URL to fetch data from with the options
            let url = `/api/toggle_report?report_id=${ID}&state=${active}`;            

            // Fetch the data and update the datasets
            fetch(url)
                .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    // Disable or Re-enable the Div Accordingly
                    if (reportDiv) {
                        reportDiv.classList.toggle('d-none', !checkbox.checked);
                    }
                })
                .catch(error => console.error('Error fetching data:', error));

        });
    });
});