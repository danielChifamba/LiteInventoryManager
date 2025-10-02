const POS={init(){this.setupCSRF(),this.setupKeyboardShortcuts(),this.setupPrintFunctionality(),this.setupAutoFocus()},setupCSRF(){document.body.addEventListener("htmx:configRequest",e=>{const t=this.getCSRFToken();t&&(e.detail.headers["X-CSRFToken"]=t)})},getCSRFToken(){const e=document.querySelector('meta[name="csrf-token"]');if(e)return e.getAttribute("content");const t=document.cookie.split(";");for(let e of t){const[n,s]=e.trim().split("=");if(n==="csrftoken")return decodeURIComponent(s)}return null},setupKeyboardShortcuts(){document.addEventListener("keydown",e=>{if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA")return;switch(e.key){case"F1":e.preventDefault(),document.getElementById("searchInput").focus();break;case"F2":e.preventDefault(),this.clearCart();break;case"Escape":const t=document.querySelector(".modal.show");t&&bootstrap.Modal.getInstance(t).hide();break}})},setupPrintFunctionality(){window.addEventListener("beforeprint",()=>{document.body.classList.add("printing")}),window.addEventListener("afterprint",()=>{document.body.classList.remove("printing")})},setupAutoFocus(){document.addEventListener("DOMContentLoaded",()=>{const e=document.getElementById("searchInput");e&&e.focus()})},clearCart(){confirm("Clear all items from cart?")&&htmx.ajax("POST",document.querySelector('[hx-post*="clear"]').getAttribute("hx-post"),"#cart-content")},completeSale(){const e=document.getElementById("checkoutBtn");e&&!e.disabled&&e.click()},selectPaymentMethod(e){const t=document.querySelector(`[hx-vals*="${e}"]`);t&&t.click()},showNotification(e,t="info"){const n=document.getElementById("alert-container");if(n){const s=`
                <div class="alert alert-${t} alert-dismissible fade show" role="alert">
                    ${e}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;n.innerHTML=s,setTimeout(()=>{const e=n.querySelector(".alert");e&&(e.classList.remove("show"),setTimeout(()=>e.remove(),300))},5e3)}},printReceipt(){const e=document.getElementById("receiptContent");if(e){const t=window.open("","_blank");t.document.write(`
                <html>
                <head>
                    <title>Receipt</title>
                    <style>
                        body { font-family: monospace; font-size: 12px; margin: 20px; }
                        .receipt { max-width: 300px; margin: 0 auto; }
                        @media print {
                            body { margin: 0; }
                            .receipt { max-width: none; }
                        }
                    </style>
                </head>
                <body>
                    <div class="receipt">
                        ${e.innerHTML}
                    </div>
                </body>
                </html>
            `),t.document.close(),t.print(),t.close()}}};document.addEventListener("DOMContentLoaded",()=>{POS.init(),document.body.addEventListener("htmx:beforeRequest",e=>{e.target.classList.contains("product-card")&&(e.target.style.opacity="0.7")}),document.body.addEventListener("htmx:afterRequest",e=>{e.target.classList.contains("product-card")&&(e.target.style.opacity="1"),e.detail.xhr.status>=400&&POS.showNotification("An error occurred. Please try again.","danger")}),document.body.addEventListener("htmx:responseError",e=>{POS.showNotification("Network error. Please check your connection.","danger")}),document.body.addEventListener("htmx:afterSwap",e=>{if(e.target.id==="productsGrid"){const e=document.getElementById("searchInput");e&&document.activeElement!==e&&e.focus()}e.target.id==="cart-content"&&console.log("Cart updated")})}),window.POS=POS