const apiBase = "";

let currentCartId = null;

const productForm = document.getElementById("product-form");
const productsContainer = document.getElementById("products");
const refreshProductsButton = document.getElementById("refresh-products");
const createCartButton = document.getElementById("create-cart");
const cartForm = document.getElementById("cart-form");
const cartIdLabel = document.getElementById("cart-id");
const cartDetails = document.getElementById("cart-details");
const orderDetails = document.getElementById("order-details");
const placeOrderButton = document.getElementById("place-order");
const refreshClusterButton = document.getElementById("refresh-cluster");
const clusterStatus = document.getElementById("cluster-status");
const toast = document.getElementById("toast");

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.className = `toast ${isError ? "error" : "success"}`;

  setTimeout(() => {
    toast.className = "toast hidden";
  }, 2500);
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }

  return data;
}

function renderProducts(products) {
  if (!products.length) {
    productsContainer.innerHTML = "<p class='empty-state'>No products yet.</p>";
    return;
  }

  productsContainer.innerHTML = products
    .map((product) => {
      const shardNumber = product.id % 2;
      return `
        <article class="card">
          <div class="card-top">
            <span class="tag">Product #${product.id}</span>
            <span class="tag alt">Shard ${shardNumber}</span>
          </div>
          <h3>${product.name}</h3>
          <p>${product.description}</p>
          <strong>$${product.price.toFixed(2)}</strong>
        </article>
      `;
    })
    .join("");
}

function renderCart(cart) {
  if (!cart) {
    cartDetails.innerHTML = "<p class='empty-state'>Create a cart to begin.</p>";
    return;
  }

  cartDetails.innerHTML = `
    <p><strong>Cart ID:</strong> ${cart.id}</p>
    <p><strong>Product IDs:</strong> ${cart.product_ids.length ? cart.product_ids.join(", ") : "Empty cart"}</p>
  `;
}

function renderOrder(result) {
  const productNames = result.products.map((product) => product.name).join(", ");

  orderDetails.innerHTML = `
    <p><strong>Order ID:</strong> ${result.order.id}</p>
    <p><strong>Cart ID:</strong> ${result.order.cart_id}</p>
    <p><strong>Total Price:</strong> $${result.order.total_price.toFixed(2)}</p>
    <p><strong>Products:</strong> ${productNames || "No products"}</p>
  `;
}

function renderClusterStatus(status) {
  if (!status.ok) {
    clusterStatus.innerHTML = `<p>${status.message}</p>`;
    return;
  }

  clusterStatus.innerHTML = `
    <p><strong>Replica Set:</strong> ${status.set}</p>
    <ul class="cluster-list">
      ${status.members
        .map(
          (member) =>
            `<li><strong>${member.name}</strong> - ${member.state} (health: ${member.health})</li>`
        )
        .join("")}
    </ul>
  `;
}

async function loadProducts() {
  const products = await request("/products");
  renderProducts(products);
}

async function loadClusterStatus() {
  const status = await request("/cluster/status");
  renderClusterStatus(status);
}

async function createCart() {
  const cart = await request("/carts", {
    method: "POST",
    body: JSON.stringify({ product_ids: [] }),
  });

  currentCartId = cart.id;
  cartIdLabel.textContent = String(currentCartId);
  renderCart(cart);
  orderDetails.innerHTML = "";
  showToast(`Cart ${cart.id} created.`);
}

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: document.getElementById("name").value.trim(),
    price: Number(document.getElementById("price").value),
    description: document.getElementById("description").value.trim(),
  };

  try {
    const createdProduct = await request("/products", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    productForm.reset();
    await loadProducts();
    showToast(`Product ${createdProduct.id} created on shard ${createdProduct.id % 2}.`);
  } catch (error) {
    showToast(error.message, true);
  }
});

refreshProductsButton.addEventListener("click", async () => {
  try {
    await loadProducts();
    showToast("Products refreshed.");
  } catch (error) {
    showToast(error.message, true);
  }
});

createCartButton.addEventListener("click", async () => {
  try {
    await createCart();
  } catch (error) {
    showToast(error.message, true);
  }
});

cartForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!currentCartId) {
    showToast("Create a cart first.", true);
    return;
  }

  const productId = Number(document.getElementById("product-id").value);

  try {
    const updatedCart = await request(`/carts/${currentCartId}/items`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId }),
    });

    renderCart(updatedCart);
    cartForm.reset();
    showToast(`Product ${productId} added to cart ${currentCartId}.`);
  } catch (error) {
    showToast(error.message, true);
  }
});

placeOrderButton.addEventListener("click", async () => {
  if (!currentCartId) {
    showToast("Create a cart first.", true);
    return;
  }

  try {
    const result = await request(`/orders/${currentCartId}`, {
      method: "POST",
    });

    renderOrder(result);
    showToast(`Order ${result.order.id} placed successfully.`);
  } catch (error) {
    showToast(error.message, true);
  }
});

refreshClusterButton.addEventListener("click", async () => {
  try {
    await loadClusterStatus();
    showToast("Cluster status refreshed.");
  } catch (error) {
    showToast(error.message, true);
  }
});

window.addEventListener("load", async () => {
  renderCart(null);

  try {
    await loadProducts();
  } catch (error) {
    showToast("Start MongoDB and FastAPI, then refresh.", true);
    productsContainer.innerHTML =
      "<p class='empty-state'>Unable to load products. Make sure the backend is running.</p>";
  }

  try {
    await loadClusterStatus();
  } catch (error) {
    clusterStatus.innerHTML =
      "<p class='empty-state'>Cluster status is unavailable until the backend and MongoDB are running.</p>";
  }
});
