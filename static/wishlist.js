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
        const rupeePrice = item.price;
        const conversionRate = 0.19;
        const mvrPrice = rupeePrice * conversionRate * 1.75;

        const card = document.createElement("div");
        card.className = "cart-item wishlist-card";
        card.setAttribute("data-id", item.id); // ✅ store id for safe remove

        card.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}">
          <div class="details">
            <h4>${item.name}</h4>
            <p>${mvrPrice.toFixed(2)} MVR</p>
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
      const card = btn.closest(".wishlist-card");
      if (card) {
        card.classList.add("fade-out");
        setTimeout(() => {
          card.remove();
          wishlistCount--;
          updateWishlistCount();

          // If wishlist is now empty, show empty text
          if (wishlistCount === 0) {
            document.getElementById("wishlist-container").innerHTML = "<p>Your wishlist is now empty!</p>";
          }
        }, 400); // match CSS animation
      }
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

// Initial load
fetchWishlistItems();
