const POS={config:{urls:{categories:"api/categories",products:"api/products",productsSearch:"api/products/search",completeSale:"api/sales/complete"},taxRate:0,currency:"$",logo:""},state:{categories:[],products:[],cart:[],selectedPaymentMethod:"cash",transactions:[],searchTimeout:null},dailyStats:{sales:0,transactions:0,itemsSold:0},init(){this.bindEvents(),this.loadCategories(),this.loadProducts(),this.setupCSRF();const e=document.getElementById("taxRate");this.config.taxRate=parseFloat(e.textContent);const t=document.getElementById("currencySymbol");this.config.currency=t.textContent;const n=document.getElementById("logoUrl");this.config.logo=n.textContent},setupCSRF(){const e=this.getCookie("csrftoken");$.ajaxSetup({beforeSend:function(t,n){!this.crossDomain&&n.type!=="GET"&&t.setRequestHeader("X-CSRFToken",e)}})},getCookie(e){let t=null;if(document.cookie&&document.cookie!==""){const n=document.cookie.split(";");for(let s=0;s<n.length;s++){const o=n[s].trim();if(o.substring(0,e.length+1)===e+"="){t=decodeURIComponent(o.substring(e.length+1));break}}}return t},bindEvents(){$("#searchInput").on("input",e=>{this.handleSearch(e)}),$("#categoryFilter").on("change",e=>{this.handleSearch(e)})},async loadCategories(){try{let t=this.config.urls.categories;const e=await $.get(t);this.state.categories=e.data||e,this.renderCategoryFilter()}catch(e){console.error("Error loading categories:",e)}},async loadProducts(){try{let t=this.config.urls.products;const e=await $.get(t);this.state.products=e.data||e,this.renderProducts(this.state.products)}catch(e){console.error("Error loading products:",e)}},handleSearch(){const n=document.querySelectorAll(".product-card");let o=document.getElementById("searchInput").value.toLowerCase(),s=document.getElementById("categoryFilter").value.toLowerCase();for(var t=0;t<n.length;t++){let e=n[t].querySelector(".product-name"),i=n[t].querySelector(".category"),a=e.textContent.toLowerCase()||e.innerHTML.toLowerCase(),r=i.textContent.toLowerCase()||i.innerHTML.toLowerCase(),c=a.includes(o),l=s==="display-all"||r===s;c&&l?n[t].classList.remove("hide"):n[t].classList.add("hide")}},renderCategoryFilter(){const e=$("#categoryFilter"),t=this.state.categories.map(e=>`<option value="${e.cid}">${e.name} (${e.item_count})</option>`).join();e.append(t)},renderProducts(e){const t=$("#productsGrid");if(e.length===0){t.html(`
                <div class="col-12 text-center text-muted py-4">
                    <i class="bi bi-box-seam mb-3"></i>
                    <p>No products available</p>
                </div>
            `);return}const n=e.map(e=>` <div class="product-card ${e.is_out_of_stock?"out-of-stock":""} ${e.is_low_stock?"low-stock":""}" onclick="${e.is_out_of_stock?"":`POS.addToCart('${e.sku}')`}">
                <span class="category" style="display: none">${e.category_id}</span>
                <div class="product-name fw-bold mb-2">${e.name}</div>
                <div class="product-price fs-5 mb-2">
                    ${this.config.currency}${parseFloat(e.selling_price).toFixed(2)}
                </div>
                <div class="product-stock text-muted mb-2">
                    Stock: ${e.stock_quantity}
                    ${e.is_low_stock?'<i class="bi bi-exclamation-triangle text-warning"></i>':""}
                    ${e.is_out_of_stock?'<i class="bi bi-x-circle text-danger"></i>':""}
                </div>
                <div class="product-sku small text-muted">${e.sku}</div>
                ${e.is_out_of_stock?'<div class="text-danger small mt-2">Out of Stock</div>':""}
            </div>
            `).join("");t.html(n)},addToCart(e){try{let t=this.state.products.find(t=>t.sku===e);if(!t){console.log("Product not found");return}if(t.stock_quantity===0){console.log("Product is out of stock");return}const n=this.state.cart.find(t=>t.sku===e);if(n){if(n.quantity>=t.stock_quantity){console.log("Cannot add more items than available in stock");return}n.quantity++}else this.state.cart.push({sku:t.sku,name:t.name,price:parseFloat(t.selling_price),cost_price:parseFloat(t.cost_price),quantity:1,max_stock:t.stock_quantity});this.renderCart(),this.updateTotals(),console.log(`${t.name} added to cart`)}catch(e){console.log("Error adding to cart:",e)}},removeFromCart(e){this.state.cart=this.state.cart.filter(t=>t.sku!==e),this.renderCart(),this.updateTotals()},renderCart(){const e=$("#cartItems");if(this.state.cart.length===0){e.html(`
            <div class="text-center text-muted py-4 d-flex flex-column justify-content-center h-100 fw-bold">
                Cart is empty<br>
                <small>Add products to start a sale</small>
            </div>
            `);return}const t=this.state.cart.map(e=>`
            <div class="cart-item">
                <div class="flex-grow-1">
                    <div class="fw-bold">${e.name}</div>
                    <div class="text-muted small">${this.config.currency}${e.price.toFixed(2)} each</div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button class="qty-btn bg-primary" onclick="POS.updateQuantity('${e.sku}', -1)">
                        <i class="bi bi-dash"></i>
                    </button>
                    <span class="mx-1 fw-bold">${e.quantity}</span>
                    <button class="qty-btn bg-primary" onclick="POS.updateQuantity('${e.sku}', 1)" 
                            ${e.quantity>=e.max_stock?"disabled":""} style="cursor:pointer;">
                        <i class="bi bi-plus"></i>
                    </button>
                </div>
                <div class="text-end">
                    <div class="fw-bold">${this.config.currency}${(e.price*e.quantity).toFixed(2)}</div>
                    <button class="remove-btn btn btn-danger" onclick="POS.removeFromCart('${e.sku}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `).join();e.html(t)},clearCart(){if(this.state.cart.length===0)return;this.state.cart=[],this.renderCart(),this.updateTotals()},updateTotals(){const e=this.state.cart.reduce((e,t)=>e+t.price*t.quantity,0),n=document.getElementById("cartTotal"),s=e*(this.config.taxRate/100),t=e+s;$("#subtotal").text(`${this.config.currency}${e.toFixed(2)}`),$("#tax").text(`${this.config.currency}${s.toFixed(2)}`),$("#total").text(`${this.config.currency}${t.toFixed(2)}`),$("#checkoutBtn").prop("disabled",this.state.cart.length===0||t<=0),this.state.cart.length===0||t<=0?n.style.display="none":n.style.display="block"},updateQuantity(e,t){const n=this.state.cart.find(t=>t.sku===e);if(!n)return;const s=n.quantity+t;if(s<=0){this.removeFromCart(e);return}if(s>n.max_stock){console.log("Cannot exceed available stock");return}n.quantity=s,this.renderCart(),this.updateTotals()},selectPaymentMethod(e){this.state.selectedPaymentMethod=e,document.querySelectorAll(".payment-btn").forEach(e=>e.classList.remove("active")),event.target.classList.add("active")},getCartTotal(){const e=this.state.cart.reduce((e,t)=>e+t.price*t.quantity,0),t=e*(this.config.taxRate/100);return e+t},async completeSale(){if(this.state.cart.length===0){console.log("Cart is empty");return}const e=this.getCartTotal(),t={payment_method:this.state.selectedPaymentMethod,subtotal:this.state.cart.reduce((e,t)=>e+t.price*t.quantity,0),tax_amount:this.state.cart.reduce((e,t)=>e+t.price*t.quantity,0)*(this.config.taxRate/100),discount_amount:0,total_amount:e,notes:"Sale Completed Successfully. Customer satisfied",items:this.state.cart.map(e=>({sku:e.sku,quantity:e.quantity,unit_price:e.price,cost_price:e.cost_price}))};try{$("#checkoutBtn").prop("disabled",!0).html('<i class="bi fa-spinner fa-spin"></i> Processing...');const e=await $.ajax({url:this.config.urls.completeSale,method:"POST",contentType:"application/json",data:JSON.stringify(t)});if(e.success)this.generateReceipt(e.sale),this.resetSale(),$("#receiptModal").modal("show"),this.loadProducts();else throw new Error(e.message||"Sale completion failed")}catch(e){console.error("Error completing sale:",e)}finally{$("#checkoutBtn").prop("disabled",!1).html('<i class="fas fa-check-circle"></i> Complete Sale')}},closeModal(){document.getElementById("receiptModal").style.display="none"},generateReceipt(e){const t=new Date,n=t.getHours().toString().padStart(2,"0"),s=t.getMinutes().toString().padStart(2,"0"),o=t.getSeconds().toString().padStart(2,"0"),i=document.getElementById("receiptContent");i.innerHTML=`
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="${this.config.logo}" alt="Business Logo" style="display: ${e.showLogo?"block":"none"};margin: 0 auto 10px;">
            <p>Transaction: ${e.sale_id}</p>
            ${e.showTime?`<p>Date: ${e.created_at} ${n}:${s}:${o}</p>`:""}
            ${e.showName?`<p>Seller: ${e.cashier_name}</p>`:""}
        </div>
        
        <div style="border-bottom: 1px dashed #ccc; margin: 15px 0;"></div>
        
        <div>
            ${e.items.map(e=>`
                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                    <span>${e.product_name} x${e.quantity}</span>
                    <span>${this.config.currency}${(e.unit_price*e.quantity).toFixed(2)}</span>
                </div>
            `).join("")}
        </div>
        
        <div style="border-bottom: 1px dashed #ccc; margin: 15px 0;"></div>
        
        <div>
            <div style="display: flex; justify-content: space-between;">
                <span>Subtotal:</span>
                <span>${this.config.currency}${e.subtotal}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>Tax:</span>
                <span>${this.config.currency}${e.tax_amount}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>TOTAL:</span>
                <span>${this.config.currency}${e.total_amount}</span>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <p>Payment Method: ${e.payment_method.toUpperCase()}</p>
            <p style="margin-top: 15px; font-size: 12px;">
                ${e.showThanks?`${e.thanksNote}<br>`:""}
                Please keep this receipt for your records.
            </p>
        </div>

        <div class="no-print" style="text-align: center; margin-top: 20px;">
            <button onclick="POS.printReceipt()" class="btn btn-primary" style="padding: 10px 20px;">
                <i class="bi bi-printer"></i> Print Receipt
            </button>
        </div>
    `},printReceipt(){const printWindow=window.open('','_blank','width=300,height=600');const receiptContent=document.getElementById('receiptContent').innerHTML;printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Receipt</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                }
                img {
                    max-width: 60px;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                }
                .no-print {
                    display: none !important;
                }
                @page {
                    size: 80mm auto;
                    margin: 0;
                }
                @media print {
                    body {
                        width: 80mm;
                        margin: 0;
                        padding: 5mm;
                    }
                    .no-print {
                        display: none !important;
                    }
                }
                @media screen {
                    body {
                        width: 80mm;
                        margin: 20px auto;
                        padding: 10px;
                        border: 1px solid #ddd;
                        background: white;
                    }
                }
            </style>
        </head>
        <body>
            ${receiptContent}
        </body>
        </html>
    `);
    printWindow.document.close();printWindow.focus();setTimeout(() => {printWindow.print();printWindow.close();},250);},resetSale(){this.state.cart=[],this.renderCart(),this.updateTotals()}}