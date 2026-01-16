/**
 * =============================================================================
 * IMAGE RESIZER AND COMPRESSOR - Frontend JavaScript
 * =============================================================================
 * 
 * This file handles all the interactive functionality of the web app:
 * - File upload and validation
 * - Form submission via AJAX
 * - Image preview display
 * - Download functionality
 * - User feedback (loading, errors, success messages)
 * 
 * =============================================================================
 */

// =============================================================================
// WAIT FOR DOM TO LOAD
// =============================================================================
// This ensures all HTML elements are available before we try to access them
document.addEventListener('DOMContentLoaded', function() {
    console.log('Image Resizer App Initialized!');
    
    // =========================================================================
    // GET DOM ELEMENTS
    // =========================================================================
    // We store references to HTML elements we'll need to manipulate
    
    // Form elements
    const uploadForm = document.getElementById('uploadForm');
    const imageInput = document.getElementById('imageInput');
    const widthInput = document.getElementById('widthInput');
    const heightInput = document.getElementById('heightInput');
    const maxSizeInput = document.getElementById('maxSizeInput');
    const qualitySlider = document.getElementById('qualitySlider');
    const qualityValue = document.getElementById('qualityValue');
    const submitBtn = document.getElementById('submitBtn');
    
    // File upload elements
    const dropZone = document.getElementById('dropZone');
    const fileSelected = document.getElementById('fileSelected');
    const fileName = document.getElementById('fileName');
    
    // Original info elements
    const originalInfo = document.getElementById('originalInfo');
    const originalDimensions = document.getElementById('originalDimensions');
    const originalFileSize = document.getElementById('originalFileSize');
    
    // Preview elements
    const previewContainer = document.getElementById('previewContainer');
    const previewPlaceholder = document.getElementById('previewPlaceholder');
    const previewImage = document.getElementById('previewImage');
    
    // Processed info elements
    const processedInfo = document.getElementById('processedInfo');
    const newDimensions = document.getElementById('newDimensions');
    const newFileSize = document.getElementById('newFileSize');
    const finalQuality = document.getElementById('finalQuality');
    const sizeReduction = document.getElementById('sizeReduction');
    
    // Download elements
    const downloadBtn = document.getElementById('downloadBtn');
    const filenameSection = document.getElementById('filenameSection');
    const filenameInput = document.getElementById('filenameInput');
    
    // Status elements
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const successMessage = document.getElementById('successMessage');
    const successText = document.getElementById('successText');
    
    // Modal elements
    const modal = document.getElementById('modal');
    const howToUse = document.getElementById('howToUse');
    const closeModal = document.getElementById('closeModal');
    
    // Preset buttons
    const presetBtns = document.querySelectorAll('.preset-btn');
    const sizePresetBtns = document.querySelectorAll('.size-preset-btn');
    
    // Store the processed image data for download
    let processedImageData = null;
    let originalFileSizeKB = 0;
    
    // =========================================================================
    // HELPER FUNCTIONS
    // =========================================================================
    
    /**
     * Show an error message to the user
     * @param {string} message - The error message to display
     */
    function showError(message) {
        // Hide success message if visible
        successMessage.style.display = 'none';
        
        // Show error message
        errorText.textContent = message;
        errorMessage.style.display = 'flex';
        errorMessage.classList.add('fade-in');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Show a success message to the user
     * @param {string} message - The success message to display
     */
    function showSuccess(message) {
        // Hide error message if visible
        errorMessage.style.display = 'none';
        
        // Show success message
        successText.textContent = message;
        successMessage.style.display = 'flex';
        successMessage.classList.add('fade-in');
    }
    
    /**
     * Show loading indicator
     */
    function showLoading() {
        loading.style.display = 'block';
        previewPlaceholder.style.display = 'none';
        previewImage.style.display = 'none';
        processedInfo.style.display = 'none';
        downloadBtn.style.display = 'none';
        filenameSection.style.display = 'none';
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
        submitBtn.disabled = true;
    }
    
    /**
     * Hide loading indicator
     */
    function hideLoading() {
        loading.style.display = 'none';
        submitBtn.disabled = false;
    }
    
    /**
     * Reset the preview section to initial state
     */
    function resetPreview() {
        previewPlaceholder.style.display = 'flex';
        previewImage.style.display = 'none';
        processedInfo.style.display = 'none';
        downloadBtn.style.display = 'none';
        filenameSection.style.display = 'none';
        processedImageData = null;
    }
    
    /**
     * Format file size to human-readable string
     * @param {number} sizeKB - Size in kilobytes
     * @returns {string} Formatted size string
     */
    function formatFileSize(sizeKB) {
        if (sizeKB < 1) {
            return `${Math.round(sizeKB * 1024)} bytes`;
        } else if (sizeKB < 1024) {
            return `${sizeKB.toFixed(2)} KB`;
        } else {
            return `${(sizeKB / 1024).toFixed(2)} MB`;
        }
    }
    
    // =========================================================================
    // QUALITY SLIDER HANDLER
    // =========================================================================
    // Updates the displayed quality value as user moves the slider
    qualitySlider.addEventListener('input', function() {
        qualityValue.textContent = this.value;
    });
    
    // =========================================================================
    // DIMENSION PRESET BUTTONS
    // =========================================================================
    // Handle clicks on preset dimension buttons
    presetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Get the preset values from data attributes
            const width = this.dataset.width;
            const height = this.dataset.height;
            
            // Update input fields
            widthInput.value = width;
            heightInput.value = height;
            
            // Update button styles (highlight selected)
            presetBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // =========================================================================
    // FILE SIZE PRESET BUTTONS
    // =========================================================================
    // Handle clicks on preset file size buttons
    sizePresetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Get the preset value from data attribute
            const size = this.dataset.size;
            
            // Update input field
            maxSizeInput.value = size;
            
            // Update button styles
            sizePresetBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // =========================================================================
    // FILE INPUT CHANGE HANDLER
    // =========================================================================
    // When user selects a file, show file info and preview
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        
        if (file) {
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                showError('Invalid file type. Please select a JPG, JPEG, or PNG file.');
                this.value = ''; // Clear the input
                return;
            }
            
            // Validate file size (max 16MB)
            const maxSize = 16 * 1024 * 1024; // 16 MB in bytes
            if (file.size > maxSize) {
                showError('File is too large. Maximum size is 16 MB.');
                this.value = '';
                return;
            }
            
            // Show file name
            fileName.textContent = file.name;
            fileSelected.classList.add('show');
            
            // Calculate and store original file size
            originalFileSizeKB = file.size / 1024;
            originalFileSize.textContent = formatFileSize(originalFileSizeKB);
            
            // Get original dimensions using FileReader and Image
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    // Display original dimensions
                    originalDimensions.textContent = `${img.width} × ${img.height} px`;
                    originalInfo.style.display = 'block';
                    
                    // Suggest dimensions in the input fields (optional)
                    // widthInput.placeholder = img.width;
                    // heightInput.placeholder = img.height;
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
            
            // Reset preview when new file is selected
            resetPreview();
        }
    });
    
    // =========================================================================
    // DRAG AND DROP HANDLERS
    // =========================================================================
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
    }
    
    // Handle dropped files
    dropZone.addEventListener('drop', function(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            imageInput.files = files;
            // Trigger change event to process the file
            imageInput.dispatchEvent(new Event('change'));
        }
    });
    
    // =========================================================================
    // FORM SUBMISSION HANDLER
    // =========================================================================
    uploadForm.addEventListener('submit', async function(e) {
        // Prevent the default form submission (page reload)
        e.preventDefault();
        
        // Validate that a file is selected
        if (!imageInput.files || imageInput.files.length === 0) {
            showError('Please select an image file first.');
            return;
        }
        
        // Validate input values
        const width = parseInt(widthInput.value);
        const height = parseInt(heightInput.value);
        const maxSize = parseFloat(maxSizeInput.value);
        const quality = parseInt(qualitySlider.value);
        
        if (isNaN(width) || width <= 0 || width > 5000) {
            showError('Width must be between 1 and 5000 pixels.');
            widthInput.focus();
            return;
        }
        
        if (isNaN(height) || height <= 0 || height > 5000) {
            showError('Height must be between 1 and 5000 pixels.');
            heightInput.focus();
            return;
        }
        
        if (isNaN(maxSize) || maxSize <= 0) {
            showError('Maximum file size must be a positive number.');
            maxSizeInput.focus();
            return;
        }
        
        // Show loading indicator
        showLoading();
        
        // Create FormData object for sending to server
        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        formData.append('width', width);
        formData.append('height', height);
        formData.append('maxSize', maxSize);
        formData.append('quality', quality);
        
        try {
            // Send POST request to the server
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            // Parse JSON response
            const data = await response.json();
            
            // Hide loading indicator
            hideLoading();
            
            if (data.success) {
                // Success! Display the processed image
                processedImageData = data.image;
                
                // Show preview image
                previewPlaceholder.style.display = 'none';
                previewImage.src = data.image;
                previewImage.style.display = 'block';
                previewImage.classList.add('fade-in');
                
                // Update processed info
                newDimensions.textContent = `${data.newWidth} × ${data.newHeight} px`;
                newFileSize.textContent = formatFileSize(data.finalSize);
                finalQuality.textContent = `${data.finalQuality}%`;
                
                // Calculate size reduction percentage
                if (originalFileSizeKB > 0) {
                    const reduction = ((originalFileSizeKB - data.finalSize) / originalFileSizeKB * 100);
                    sizeReduction.textContent = reduction > 0 
                        ? `${reduction.toFixed(1)}% smaller` 
                        : 'No reduction';
                }
                
                processedInfo.style.display = 'block';
                processedInfo.classList.add('fade-in');
                
                // Show download button
                downloadBtn.style.display = 'flex';
                downloadBtn.classList.add('fade-in');
                
                // Show filename section
                filenameSection.style.display = 'block';
                
                // Show success message
                showSuccess(data.message);
                
            } else {
                // Error from server
                showError(data.error || 'An error occurred while processing the image.');
            }
            
        } catch (error) {
            // Network or other error
            hideLoading();
            console.error('Error:', error);
            showError('Failed to connect to the server. Please try again.');
        }
    });
    
    // =========================================================================
    // DOWNLOAD BUTTON HANDLER
    // =========================================================================
    downloadBtn.addEventListener('click', async function() {
        if (!processedImageData) {
            showError('No processed image available. Please process an image first.');
            return;
        }
        
        // Get custom filename
        let customFilename = filenameInput.value.trim();
        
        // Validate and sanitize filename
        if (!customFilename) {
            customFilename = 'resized_image.jpg';
        } else if (!customFilename.endsWith('.jpg') && !customFilename.endsWith('.jpeg')) {
            customFilename += '.jpg';
        }
        
        try {
            // Method 1: Direct download using data URL (simpler)
            const link = document.createElement('a');
            link.href = processedImageData;
            link.download = customFilename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showSuccess('Image downloaded successfully!');
            
        } catch (error) {
            console.error('Download error:', error);
            
            // Method 2: Fallback - use server endpoint
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        image: processedImageData,
                        filename: customFilename
                    })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = customFilename;
                    document.body.appendChild(link);
                    link.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                    showSuccess('Image downloaded successfully!');
                } else {
                    const data = await response.json();
                    showError(data.error || 'Download failed.');
                }
            } catch (fallbackError) {
                showError('Download failed. Please try again.');
            }
        }
    });
    
    // =========================================================================
    // MODAL HANDLERS
    // =========================================================================
    // Open modal
    howToUse.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'flex';
    });
    
    // Close modal - close button
    closeModal.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Close modal - click outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Close modal - Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });
    
    // =========================================================================
    // INPUT VALIDATION - Real-time feedback
    // =========================================================================
    // Width validation
    widthInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (value > 5000) {
            this.value = 5000;
        } else if (value < 1 && this.value !== '') {
            this.value = 1;
        }
    });
    
    // Height validation
    heightInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (value > 5000) {
            this.value = 5000;
        } else if (value < 1 && this.value !== '') {
            this.value = 1;
        }
    });
    
    // Max size validation
    maxSizeInput.addEventListener('input', function() {
        const value = parseFloat(this.value);
        if (value > 10240) {
            this.value = 10240;
        } else if (value < 1 && this.value !== '') {
            this.value = 1;
        }
    });
    
    // =========================================================================
    // KEYBOARD SHORTCUTS
    // =========================================================================
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (imageInput.files && imageInput.files.length > 0) {
                uploadForm.dispatchEvent(new Event('submit'));
            }
        }
    });
    
    // =========================================================================
    // INITIALIZATION COMPLETE
    // =========================================================================
    console.log('All event handlers registered successfully!');
});