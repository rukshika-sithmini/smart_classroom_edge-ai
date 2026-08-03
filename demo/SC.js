// --- LIVE FEED (Python Backend AI Video Analytics) ---
function fetchLiveFeedStatus() {
    fetch('/api/live_status')
        .then(response => response.json())
        .then(data => {
            // Update Live Occupancy Card
            let livePeopleCountEl = document.getElementById("live-people-count");
            let liveOccupancyLevelEl = document.getElementById("live-occupancy-level");
            let liveOccupancyPanelEl = document.getElementById("live-occupancy-panel");

            if (livePeopleCountEl) livePeopleCountEl.textContent = data.people_count;
            if (liveOccupancyLevelEl) liveOccupancyLevelEl.textContent = data.occupancy_level;
            
            if (liveOccupancyPanelEl) {
                let levelLower = data.occupancy_level.toLowerCase();
                liveOccupancyPanelEl.className = "card1 " + levelLower;
            }

            // Update Live AC Card
            let liveAcIndicatorEl = document.getElementById("live-ac-indicator");
            let liveAcStateTextEl = document.getElementById("live-ac-state-text");
            let liveAcTempEl = document.getElementById("live-ac-temp");
            let liveAcLastChangedEl = document.getElementById("live-ac-last-changed");
            let liveAcRunTimeEl = document.getElementById("live-ac-run-time");

            if (data.ac_state === "ON") {
                if (liveAcIndicatorEl) liveAcIndicatorEl.className = "ac-indicator on";
                if (liveAcStateTextEl) {
                    liveAcStateTextEl.className = "ac-state-text on";
                    liveAcStateTextEl.textContent = "ON";
                }
            } else {
                if (liveAcIndicatorEl) liveAcIndicatorEl.className = "ac-indicator off";
                if (liveAcStateTextEl) {
                    liveAcStateTextEl.className = "ac-state-text off";
                    liveAcStateTextEl.textContent = "OFF";
                }
            }

            if (liveAcTempEl) liveAcTempEl.textContent = data.ac_temp;
            if (liveAcLastChangedEl) liveAcLastChangedEl.textContent = data.ac_last_changed;
            if (liveAcRunTimeEl) liveAcRunTimeEl.textContent = data.ac_run_time || "00:00:00";

            // Update AI Prediction Confidence Card
            let confidenceValEl = document.getElementById("live-confidence-value");
            let confidenceBadgeEl = document.getElementById("live-confidence-badge");
            let confidenceBarEl = document.getElementById("live-confidence-bar");
            let studentCountEl = document.getElementById("live-student-count");
            let cleanerCountEl = document.getElementById("live-cleaner-count");

            if (confidenceValEl) confidenceValEl.textContent = data.avg_confidence;
            if (studentCountEl) studentCountEl.textContent = data.student_count;
            if (cleanerCountEl) cleanerCountEl.textContent = data.cleaner_count;

            if (confidenceBarEl) {
                confidenceBarEl.style.width = (data.confidence_val || 0) + "%";
            }

            if (confidenceBadgeEl) {
                let conf = data.confidence_val || 0;
                if (conf >= 80) {
                    confidenceBadgeEl.textContent = "HIGH CONFIDENCE";
                    confidenceBadgeEl.style.color = "#22c55e";
                    confidenceBadgeEl.style.borderColor = "rgba(34, 197, 94, 0.4)";
                    confidenceBadgeEl.style.background = "rgba(34, 197, 94, 0.15)";
                } else if (conf >= 50) {
                    confidenceBadgeEl.textContent = "FAIR CONFIDENCE";
                    confidenceBadgeEl.style.color = "#eab308";
                    confidenceBadgeEl.style.borderColor = "rgba(234, 179, 8, 0.4)";
                    confidenceBadgeEl.style.background = "rgba(234, 179, 8, 0.15)";
                } else if (conf > 0) {
                    confidenceBadgeEl.textContent = "LOW CONFIDENCE";
                    confidenceBadgeEl.style.color = "#ef4444";
                    confidenceBadgeEl.style.borderColor = "rgba(239, 68, 68, 0.4)";
                    confidenceBadgeEl.style.background = "rgba(239, 68, 68, 0.15)";
                } else {
                    confidenceBadgeEl.textContent = "NO DETECTIONS";
                    confidenceBadgeEl.style.color = "#94a3b8";
                    confidenceBadgeEl.style.borderColor = "rgba(148, 163, 184, 0.3)";
                    confidenceBadgeEl.style.background = "rgba(148, 163, 184, 0.1)";
                }
            }

            // Update Active File / Source Info
            let activeFilenameEl = document.getElementById("current-video-filename");
            if (activeFilenameEl && data.current_video) {
                activeFilenameEl.textContent = data.current_video;
            }
        })
        .catch(err => {
            console.error("Error fetching live status from Python backend:", err);
        });
}

// Poll live status every 800ms
fetchLiveFeedStatus();
setInterval(fetchLiveFeedStatus, 800);


// --- FILE UPLOAD & LIVE CAMERA HANDLING ---
function setupUploadHandler() {
    let uploadBtnTrigger = document.getElementById("upload-btn-trigger");
    let uploadInput = document.getElementById("video-upload-input");
    let liveCamBtnTrigger = document.getElementById("live-camera-btn");
    let uploadStatusText = document.getElementById("upload-status");

    if (uploadBtnTrigger && uploadInput) {
        uploadBtnTrigger.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadInput.click();
        });
    }

    if (liveCamBtnTrigger) {
        liveCamBtnTrigger.addEventListener("click", (e) => {
            e.preventDefault();
            if (uploadStatusText) {
                uploadStatusText.textContent = "Connecting to Live WebCam...";
                uploadStatusText.style.color = "#38bdf8";
            }

            fetch('/api/start_camera', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_index: 0 })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (uploadStatusText) {
                        uploadStatusText.textContent = "✓ Connected to Live WebCam!";
                        uploadStatusText.style.color = "#22c55e";
                    }
                    let imgEl = document.getElementById("live-video-feed");
                    if (imgEl) {
                        imgEl.src = "/video_feed?t=" + new Date().getTime();
                    }
                } else {
                    if (uploadStatusText) {
                        uploadStatusText.textContent = "❌ " + (data.error || "WebCam failed");
                        uploadStatusText.style.color = "#ef4444";
                    }
                }
            })
            .catch(err => {
                if (uploadStatusText) {
                    uploadStatusText.textContent = "❌ Could not access live camera";
                    uploadStatusText.style.color = "#ef4444";
                }
                console.error("Camera error:", err);
            });
        });
    }

    if (uploadInput) {
        uploadInput.addEventListener("change", (e) => {
            let file = e.target.files[0];
            if (!file) return;

            let formData = new FormData();
            formData.append("video", file);

            if (uploadStatusText) {
                uploadStatusText.textContent = "Uploading...";
                uploadStatusText.style.color = "#38bdf8";
            }

            fetch('/api/upload_video', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (uploadStatusText) {
                        uploadStatusText.textContent = "✓ Uploaded & Processing!";
                        uploadStatusText.style.color = "#22c55e";
                    }
                    
                    let imgEl = document.getElementById("live-video-feed");
                    if (imgEl) {
                        imgEl.src = "/video_feed?t=" + new Date().getTime();
                    }
                } else {
                    if (uploadStatusText) {
                        uploadStatusText.textContent = "❌ " + (data.error || "Upload failed");
                        uploadStatusText.style.color = "#ef4444";
                    }
                }
            })
            .catch(err => {
                if (uploadStatusText) {
                    uploadStatusText.textContent = "❌ Error uploading video";
                    uploadStatusText.style.color = "#ef4444";
                }
                console.error("Upload error:", err);
            });
        });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupUploadHandler);
} else {
    setupUploadHandler();
}