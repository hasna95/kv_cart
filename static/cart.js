function updateCartDisplay() {
  fetch('/api/cart')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("cart-container");
      container.innerHTML = "";

      let totalQuantity = 0;
      let totalPriceInMvr = 0;
      const conversionRate = 0.19;

      if (data.length === 0) {
        container.innerHTML = "<p>Your cart is empty!</p>";
        updateCartCount();
        return;
      }

      data.forEach(item => {
        const rupeePrice = item.price;
        const mvrPricePerUnit = rupeePrice * conversionRate * 1.75;
        const totalMvrPriceForItem = mvrPricePerUnit * item.quantity;

        const div = document.createElement("div");
        div.className = "cart-item";

        // ✅ Build size HTML if size available
        const sizeHTML = item.size ? `<p><strong>Size:</strong> ${item.size}</p>` : "";

        div.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}">
          <div class="details">
            <h4>${item.name}</h4>
            ${sizeHTML} <!-- ✅ Insert size info if exists -->
            <p>Price per unit: ${mvrPricePerUnit.toFixed(2)} MVR</p>
            <div class="quantity">
              <button onclick="changeQuantity(${item.product_id}, ${item.quantity - 1})">-</button>
              <input type="number" value="${item.quantity}" onchange="changeQuantity(${item.product_id}, this.value)">
              <button onclick="changeQuantity(${item.product_id}, ${item.quantity + 1})">+</button>
            </div>
          </div>
          <button class="remove" onclick="changeQuantity(${item.product_id}, 0)">❌</button>
        `;
        container.appendChild(div);

        totalQuantity += item.quantity;
        totalPriceInMvr += totalMvrPriceForItem;
      });

      // ✅ Add cart summary at the bottom
      const summaryDiv = document.createElement("div");
      summaryDiv.className = "cart-summary";
      summaryDiv.innerHTML = `
        <h3>Cart Summary</h3>
        <p><strong>Total Items:</strong> ${totalQuantity}</p>
        <p><strong>Total Price:</strong> ${totalPriceInMvr.toFixed(2)} MVR</p>
        <a href="/dashboard" class="add-to-cart-btn" style="margin-top: 10px;">⬅ Back to Dashboard</a>
      `;
      container.appendChild(summaryDiv);

      updateCartCount();
    });
}

function changeQuantity(productId, newQty) {
  fetch('/api/cart/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, quantity: parseInt(newQty) })
  }).then(() => updateCartDisplay());
}

function updateCartCount() {
  fetch('/api/cart/count')
    .then(res => res.json())
    .then(data => {
      document.getElementById("cart-count").innerText = data.count;
    });
}

updateCartDisplay();
