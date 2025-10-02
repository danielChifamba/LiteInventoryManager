document.getElementById("resetForm").addEventListener("submit",function(e){const t=document.getElementById("password").value,n=document.getElementById("confirm_password").value;if(t!==n){e.preventDefault(),alert("Passwords do not match!");return}if(t.length<=7){e.preventDefault(),alert("Password must be 8 characters long!");return}document.getElementById("loading").style.display="block",document.getElementById("submitBtn").disabled=!0,document.getElementById("submitBtn").textContent="Processing..."});function resetPasswordPopup(){const t=450,n=600,s=(screen.width-t)/2,o=(screen.height-n)/2,i=`
        width=${t},
        height=${n},
        left=${s},
        right=${o},
        scrollbars=yes,
        resizable=yes,
        status=no,
        location=no,
        toolbar=no,
        menubar=no
    `,e=window.open("/password_reset/","passwordResetPopup",i);e&&e.focus();const a=setInterval(function(){e.closed&&(clearInterval(a),console.log("Password reset popup was closed"))},1e3)}