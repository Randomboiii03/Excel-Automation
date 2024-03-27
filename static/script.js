window.onload = function () {
  const socket = io();
  socket.connect("http://localhost:8000");

  const bankName = document.getElementById("bank_name");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const mergeButton = document.getElementById("mergeButton");
  const progressContainer = document.getElementById("progress");
  const messageContainer = document.getElementById("message");
  const messageStatus = document.getElementById("messageStatus");
  const messageText = document.getElementById("messageText");
  const mergeForm = document.getElementById("mergeForm");
  const hiddenClasses = ["hidden"];
  const successClasses = ["bg-green-100", "border-green-400", "text-green-700"];
  const errorClasses = ["bg-red-100", "border-red-400", "text-red-700"];

  let folderPath = "";

  socket.on("connect", function () {
    console.log("Connected!");
  });

  socket.on("update progress", function (percent) {
    console.log("Got percent: " + percent);
    animateProgress(percent);
  });

  function animateProgress(targetPercent) {
    let currentPercent = parseFloat(progressBar.style.width) || 0;
    const step = (targetPercent - currentPercent) / 20;
    const interval = setInterval(function () {
      currentPercent += step;
      progressBar.style.width = currentPercent + "%";
      progressText.textContent = Math.round(currentPercent) + "%";
      if (currentPercent >= targetPercent) {
        clearInterval(interval);
      }
    }, 50);
  }

  function showMessage(message, status, classes) {
    messageText.innerHTML = message;
    messageStatus.innerHTML = status;
    messageContainer.classList.remove(
      ...hiddenClasses,
      ...successClasses,
      ...errorClasses
    );
    messageContainer.classList.add(...classes);
    mergeButton.classList.remove(...hiddenClasses);
    progressContainer.classList.add(...hiddenClasses);
    bankName.disabled = false;
  }

  function deleteFiles() {
    fetch("/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data: folderPath,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        Swal.fire({
            icon: 'success',
            title: data.message,
            timer: 5000, // Adjust as needed
            
            timerProgressBar: true,
            toast: true,
            position: 'center',
            showConfirmButton: false,
            customClass: {
              popup: 'toast-custom-class-info',
              backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
            }
          });
      })
      .catch((error) => {
        showMessage(error, "Error!", errorClasses);
      });
  }

  function showDeleteModal() {
    $("#delete-modal").removeClass("hidden");
  }

  function hideDeleteModal() {
    $("#delete-modal").addClass("hidden");
  }

  $("#delete-confirm-button").on("click", function () {
    deleteFiles();
    hideDeleteModal();
  });

  $("#delete-cancel-button").on("click", function () {
    hideDeleteModal();
    Swal.fire({
        icon: 'info',
        title: 'Files under this campaign are safe!',
        timer: 5000, // Adjust as needed
        timerProgressBar: true,
        toast: true,
        position: 'center',
        showConfirmButton: false,
        customClass: {
          popup: 'toast-custom-class',
          backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
        }
      });
  });

  mergeForm.onsubmit = function (event) {
    event.preventDefault();
    const formData = new FormData(mergeForm);
    bankName.disabled = true;
    fetch("/merge", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        const classes = data.status ? successClasses : errorClasses;
        showMessage(data.message, data.status ? "Success!" : "Error!", [
          ...classes,
        ]);
        if (data.status) {
          Swal.close();
          folderPath = data.file_path;
       
          hideDeleteModal();
          showDeleteModal();
        }
      })
      .catch((error) => {
        showMessage(error, "Error!", errorClasses);
      });
  };

  mergeButton.addEventListener("click", function () {
    mergeButton.classList.add(...hiddenClasses);
    progressContainer.classList.remove(...hiddenClasses);
    progressBar.style.width = 0 + "%";
    progressText.textContent = Math.round(0) + "%";
    messageContainer.classList.add(...hiddenClasses);
  });

  window.addEventListener("keydown", function (event) {
    if (
      event.keyCode === 116 &&
      !document.getElementById("progress").classList.contains("hidden")
    ) {
      // Prevent default behavior
      event.preventDefault();
      event.returnValue = ""; // For older browsers
      // Display SweetAlert confirmation
      Swal.fire({
        // title: "Ongoing Merging Process",
        text: "There is an ongoing merging process. Are you sure you want to leave?",
        iconHtml: '<i class="fa fa-refresh fa-spin" style="color:black;"></i>',
        showCancelButton: true,
        confirmButtonColor: "#bf3232",
        cancelButtonColor: "#05b531",
        confirmButtonText: "Yes, leave",
        cancelButtonText: "No, stay",
        reverseButtons: true, // To swap the positions of the buttons
        customClass: {
          popup: "smaller-sweetalert", // Custom class for the popup
        },
      }).then((result) => {
        if (result.isConfirmed) {
          // Proceed with leaving
          location.reload();
        } else {
          // Stay on the page
          // Do nothing
        }
      });
    }
  });
};

var invalidAttempts = 0;


function toggleForm(formToShow) {
  var forms = ["geocodeForm", "dataFeedForm", "mergeit"];
  forms.forEach(function (formId) {
    var form = document.getElementById(formId);
    form.style.display = formToShow === formId ? "block" : "none";
  });
}


function promptForPassword(formToShow) {
  if (formToShow === "dataFeedForm") {
    Swal.fire({
      html: '<p style="color:#C58376;"><strong>Security Authentication</strong><p>',
      input: "password",
      inputAttributes: {
        autocapitalize: "off",
        style:
          "height: 40px; border-radius: 10px;  border: 1px solid #ccc; outline: none;", // Adjust the max-width as needed
      },
      showCancelButton: true,
      confirmButtonText: "Submit",
      preConfirm: (password) => {
        if (password === "123") {
          // Replace '123' with your actual password
          toggleForm(formToShow);
          Swal.fire({
            icon: 'success',
            title: 'Login Successful!',
            timer: 5000, // Adjust as needed
            timerProgressBar: true,
            toast: true,
            position: 'center',
            showConfirmButton: false,
            customClass: {
              popup: 'toast-custom-class',
              backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
            }
          });
        } else {
          invalidAttempts++;
          if (invalidAttempts >= 3) {
            let countdown = 60; // initial countdown value
            

            document.getElementById('overlay').classList.remove('overlay-hidden');  

            Swal.fire({
              icon: "error",
              title: "Cooldown " + countdown + " seconds",
              timer: 60000, // update every second
              timerProgressBar: false,
              toast: true,
              showConfirmButton: false,
              allowOutsideClick: false,
              
              onBeforeOpen: () => {
                const content = Swal.getContent();
                if (content) {
                  const timerInterval = setInterval(() => {
                    countdown--;
                    if (countdown >= 0) {
                      Swal.getTitle().textContent =
                        "Cooldown " + countdown + " seconds";
                    } else {
                      clearInterval(timerInterval);
                      Swal.close();

                      // fetch('/sleep')
                      //     .then(response => response.text())
                      //     .then(data => console.log(data))
                      //     .catch(error => console.error('Error:', error));
                      document.getElementById('overlay').classList.add('overlay-hidden');
                    }
                  }, 1000);
                }
              },
              customClass: {
                popup: 'toast-custom-class-cool',
                backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
              }
            });
            
          } else {
            // Swal.fire({
            //   html: '<i class="fas fa-exclamation-circle" style="font-size: 24px; color:red;"></i> Invalid input.',
            //   confirmButtonText: "RETRY",
            //   timer: 10000,
            // });
            Swal.fire({
                icon: 'error',
                title: 'Invalid input',
                timer: 5000, // Adjust as needed
                timerProgressBar: true,
                toast: true,
                position: 'center',
                showConfirmButton: false,
                customClass: {
                  popup: 'toast-custom-class-false',
                  backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
                }
              });
          }
        }
      },
      footer: '<a href="#">Contact Developers</a>',
    });
  } else {
    toggleForm(formToShow);
  }
}


document.addEventListener("DOMContentLoaded", function () {
  const navbarToggle = document.getElementById("navbar-toggle");
  const navbar = document.querySelector(".navbar");
  navbar.style.transform = "translateY(-100%)";
  navbarToggle.addEventListener("change", function () {
    if (navbarToggle.checked) {
      navbar.style.transform = "translateY(0)";
    } else {
      navbar.style.transform = "translateY(-100%)";
    }
  });

  const uploadForm = document.getElementById("uploadForm");
  const fileInput = document.getElementById("fileInput");

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("file", file);

    // Loading

    try {
      const response = await fetch("/predict", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.text();

      // Handle successful upload response
      console.log(data);
      // Trigger Sweet Alert notification
      Swal.fire({
        icon: 'success',
        title: 'File processing completed',
        timer: 5000, // Adjust as needed
        timerProgressBar: true,
        toast: true,
        position: 'center',
        showConfirmButton: false,
        customClass: {
          popup: 'toast-custom-class',
          backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
        }
      });
    } catch (error) {
      // Handle errors
      console.error("There was an error with the upload:", error);
      // Optionally, trigger an error Sweet Alert notification
     
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("uploadFeed").addEventListener("submit", (e) => {
    e.preventDefault();
    let formData = new FormData();
    formData.append("file", document.getElementById("file").files[0]);
    Swal.fire({
      title:
        '<h6 style="font-size:25px;"> <i class="fas fa-spinner animated-spinner"></i> DATA IS CURRENTLY FEEDING <div class="custom-line"></div></h6>',
      html: '<p style="color:red; font-size:12px; text-align:left; "><strong>Note:</strong> Interrupting or canceling this process may result in corruption of the model.</p>',

      allowOutsideClick: false,
      showConfirmButton: false,
      willOpen: () => {
        // Swal.showLoading()
      },
    });
    fetch("/feed", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        Swal.close(); 
        if (data.status) {
          Swal.fire({
            icon: "success",
            title: data.message,
            timer: 5000, // Adjust as needed
            toast: true,
            position: 'center',
            showConfirmButton: false,
            customClass: {
              popup: 'toast-custom-class',
              backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
            }
          });
        } else {
          Swal.fire({
            icon: "error",
            title: data.message,
            timer: 5000, // Adjust as needed
            timerProgressBar: true,
            toast: true,
            position: 'center',
            showConfirmButton: false,
            customClass: {
              popup: 'toast-custom-class-false',
              backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
            }
          });
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        Swal.fire({
          icon: "error",
          title: "An error occurred while processing the request.",
          timer: 5000, // Adjust as needed
          timerProgressBar: true,
          toast: true,
          position: 'center',
          showConfirmButton: false,
          customClass: {
            popup: 'toast-custom-class-false',
            backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
          }
        });
      });
  });
});

function showLoader() {
  document.getElementById("uploadText").style.display = "none"; // Hide the upload text
  document.getElementById("loader").style.display = "block"; // Show the loader
}

function toggleTooltip() {
  var tooltip = document.getElementById("tooltipContent");
  if (tooltip.classList.contains("hidden")) {
    tooltip.classList.remove("hidden");
  } else {
    tooltip.classList.add("hidden");
  }
}

function showTooltip() {
  document.getElementById("tooltipContent").classList.remove("hidden");
}

function hideTooltip() {
  document.getElementById("tooltipContent").classList.add("hidden");
}

    function showLoading() {
        var fileInput = document.getElementById('fileInput');
        if (fileInput.files.length === 0) {
            // If no file is selected, show error message
            Swal.fire({
                icon: 'error',
                title: 'Please Input a File.',
                timer: 5000, // Adjust as needed
                timerProgressBar: true,
                toast: true,
                position: 'center',
                showConfirmButton: false,
                customClass: {
                popup: 'toast-custom-class-false',
                backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
                }
            });
        } else {
            // Check if the selected file is valid (xlsx or xls)
            var validExtensions = ['xlsx', 'xls'];
            var fileName = fileInput.files[0].name;
            var fileExtension = fileName.split('.').pop().toLowerCase();
            if (!validExtensions.includes(fileExtension)) {
                // If the file extension is not valid, show error message
               
                Swal.fire({
                icon: 'error',
                title: 'Invalid File Type.',
                text: 'Please select a valid Excel file (xlsx or xls).',
                timer: 5000, // Adjust as needed
                timerProgressBar: true,
                toast: true,
                position: 'center',
                showConfirmButton: false,
                customClass: {
                popup: 'toast-custom-class-false',
                backdrop: 'toast-backdrop-class' // Add custom class for the backdrop if needed
                }
            });
            } else {
                // Show the loading screen
                Swal.fire({
                    title: '<h6 style="font-size:25px;"> <i class="fas fa-spinner animated-spinner"></i> PREDICTING <div class="custom-line"></div></h6>',
                    html: '<p style="color:red; font-size:12px; text-align:left; "><strong>Note:</strong> Interrupting or canceling this process may affect the prediction result.</p>',
                    allowOutsideClick: false,
                    showConfirmButton: false,
                    willOpen: () => {
                        // Submit the form
                        document.getElementById('uploadForm').submit();
                    },
                });
            }
        }
    }
