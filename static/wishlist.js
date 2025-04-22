let wishlistCount = 0;

function fetchWishlistItems() {
  fetch('/api/wishlist/items')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("wishlist-container");
      container.innerHTML = "";

      if (data.length === 0) {
        container.innerHTML = "<p>Your wishlist is empty!</p>";
        updateWishlistCount();
        return;
      }

      data.forEach(item => {
        const card = document.createElement("div");
        card.className = "cart-item";
        card.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}">
          <div class="details">
            <h4>${item.name}</h4>
            <p>₹ ${item.price.toFixed(2)}</p>
          </div>
          <button class="wishlist-btn active" onclick="removeWishlistItem(${item.id}, this)">♥</button>
        `;
        container.appendChild(card);
      });

      updateWishlistCount();
    });
}

function removeWishlistItem(productId, btn) {
  fetch('/api/wishlist/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "removed") {
      btn.closest(".cart-item").remove();
      wishlistCount--;
      updateWishlistCount();
    }
  });
}

function clearWishlist() {
  fetch('/api/wishlist/clear', {
    method: 'POST'
  }).then(() => {
    wishlistCount = 0;
    document.getElementById("wishlist-container").innerHTML = "<p>Your wishlist is now empty!</p>";
    updateWishlistCount();
  });
}

function updateWishlistCount() {
  fetch('/api/wishlist/count')
    .then(res => res.json())
    .then(data => {
      wishlistCount = data.count;
      document.getElementById("wishlist-count").innerText = wishlistCount;
    });
}

fetchWishlistItems();
