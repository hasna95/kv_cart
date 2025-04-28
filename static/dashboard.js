let wishlistCount = 0;


function updateWishlistIcon(icon, active) {
  if (active) {
    icon.classList.add("active");
    icon.title = "Remove from wishlist";
  } else {
    icon.classList.remove("active");
    icon.title = "Add to wishlist";
  }
}

function updateWishlistCountDisplay() {
  document.getElementById("wishlist-count").innerText = wishlistCount;
}

function toggleWishlist(productId, icon) {
  fetch('/api/wishlist/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId })
  })
  .then(res => {
    if (res.status === 401) {
      openLoginModal(() => toggleWishlist(productId, icon)); // 👈 After login, retry
      return;
    }
    return res.json();
  })
  .then(data => {
    if (!data) return;
    if (data.status === "added") {
      wishlistCount++;
      updateWishlistIcon(icon, true);
    } else if (data.status === "removed") {
      wishlistCount--;
      updateWishlistIcon(icon, false);
    }
    updateWishlistCountDisplay();
  });
}

function populateCarousel(apiUrl, containerId) {
  const container = document.getElementById(containerId);

  // STEP 1: Prepare wrapper and carousel
  const wrapper = document.createElement("div");
  wrapper.className = "carousel-wrapper";

  const carousel = document.createElement("div");
  carousel.className = "carousel";

  // STEP 2: Add 5 skeleton cards
  for (let i = 0; i < 5; i++) {
    const skeleton = document.createElement("div");
    skeleton.className = "carousel-skeleton";
    carousel.appendChild(skeleton);
  }

  // STEP 3: Add arrows NOW (even for skeletons!)
  const left = document.createElement("button");
  left.className = "carousel-nav carousel-left";
  left.innerHTML = "←";
  left.onclick = () => carousel.scrollBy({ left: -300, behavior: "smooth" });

  const right = document.createElement("button");
  right.className = "carousel-nav carousel-right";
  right.innerHTML = "→";
  right.onclick = () => carousel.scrollBy({ left: 300, behavior: "smooth" });

  wrapper.appendChild(left);
  wrapper.appendChild(carousel);
  wrapper.appendChild(right);

  container.appendChild(wrapper);

  // STEP 4: Fetch real data
  fetch(apiUrl)
    .then(res => res.json())
    .then(data => {
      carousel.innerHTML = "";  // ✅ Clear skeletons

      data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'item';

        const heart = document.createElement('button');
        heart.className = 'wishlist-btn';
        heart.innerHTML = '♥';
        heart.title = "Add to wishlist";
        heart.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleWishlist(item.id, heart);
        });

        const conversionRate = 0.19;
        const displayPriceMvr = item.price * conversionRate * 1.75;

        div.innerHTML = `
          <img src="${item.image_url}" alt="${item.name}">
          <h4>${item.name}</h4>
          <p>${displayPriceMvr.toFixed(2)} MVR</p>
        `;

        div.addEventListener('click', () => {
          window.location.href = '/product/' + item.id;
        });

        div.appendChild(heart);
        carousel.appendChild(div);
      });
    });
}


function fetchWishlistCount() {
  fetch('/api/wishlist/count')
    .then(res => res.json())
    .then(data => {
      wishlistCount = data.count;
      updateWishlistCountDisplay();
    });
}
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.innerText = message;
  toast.className = "toast show";
  setTimeout(() => {
    toast.className = toast.className.replace("show", "");
  }, 3000);
}

function addToCart(productId, quantity, size) {
  fetch('/api/cart/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      product_id: productId,
      quantity: quantity,
      size: size || null
    })
  })
  .then(res => {
    if (res.status === 401) {
      openLoginModal(() => addToCart(productId, quantity, size)); // 👈 After login, retry
      return;
    }
    return res.json();
  })
  .then(data => {
    if (!data) return;
    if (data.status === "success") {
      showToast("✅ Added to cart!");
    } else if (data.error) {
      showToast(`Error: ${data.error}`);
    }
  })
  .catch(err => {
    console.error("Failed to add product to cart:", err);
    alert("An error occurred. Please try again.");
  });
}



function updateCartCount() {
  fetch('/api/cart/count')
    .then(res => res.json())
    .then(data => {
      document.getElementById("cart-count").innerText = data.count;
    });
}

populateCarousel('/api/women-gowns', 'women-gowns-carousel');
populateCarousel('/api/one-piece-prayer-dress', 'one-piece-prayer-dress-carousel');
fetchWishlistCount();
updateCartCount();
