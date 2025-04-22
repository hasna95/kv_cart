function updateCartDisplay() {
  fetch('/api/cart')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("cart-container");
      container.innerHTML = "";

      if (data.length === 0) {
        container.innerHTML = "<p>Your cart is empty!</p>";
        updateCartCount();
        return;
      }

      data.forEach(item => {
        const div = document.createElement("div");
        div.className = "cart-item";
        div.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}">
          <div class="details">
            <h4>${item.name}</h4>
            <p>Price: ₹ ${item.price.toFixed(2)}</p>
            <div class="quantity">
              <button onclick="changeQuantity(${item.product_id}, ${item.quantity - 1})">-</button>
              <input type="number" value="${item.quantity}" onchange="changeQuantity(${item.product_id}, this.value)">
              <button onclick="changeQuantity(${item.product_id}, ${item.quantity + 1})">+</button>
            </div>
          </div>
          <button class="remove" onclick="changeQuantity(${item.product_id}, 0)">❌</button>
        `;
        container.appendChild(div);
      });

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
