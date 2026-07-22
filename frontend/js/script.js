const API_BASE_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.protocol === "file:"
    ? "http://127.0.0.1:5000"
    : "https://momi-repairing-works.onrender.com";


const api = {
  publicData: `${API_BASE_URL}/api/public/site-data`,
  adminSession: `${API_BASE_URL}/api/admin/session`,
  adminDashboard: `${API_BASE_URL}/api/admin/dashboard-data`,
  login: `${API_BASE_URL}/api/admin/login`,
  logout: `${API_BASE_URL}/api/admin/logout`,
  businessInfo: `${API_BASE_URL}/api/admin/business-info`,
  serviceDescriptions: `${API_BASE_URL}/api/admin/service-descriptions`,
  enquiries: `${API_BASE_URL}/api/public/enquiries`,
  orders: `${API_BASE_URL}/api/public/orders`,
  adminEnquiries: `${API_BASE_URL}/api/admin/enquiries`,
  adminOrders: `${API_BASE_URL}/api/admin/orders`,
  photos: (category) => `${API_BASE_URL}/api/admin/photos/${category}`,
  photoItem: (category, id) => `${API_BASE_URL}/api/admin/photos/${category}/${id}`,
  enquiryItem: (id) => `${API_BASE_URL}/api/admin/enquiries/${id}`,
  orderItem: (id) => `${API_BASE_URL}/api/admin/orders/${id}`,
};

const galleryPlaceholders = {
  admin: "Admin photos will appear here.",
  agriculture: "Agriculture machine photos will appear here.",
  doors: "Main door photos will appear here.",
  chogaths: "Chogath photos will appear here.",
};

const dashboardState = {
  enquiries: [],
  orders: [],
};

const agricultureMachineCatalog = [
  {
    value: "plough",
    label: "Plough (हल)",
    minWeight: 30,
    maxWeight: 100,
  },
  {
    value: "harrow",
    label: "Harrow (हैरो)",
    minWeight: 80,
    maxWeight: 200,
  },
  {
    value: "seed-drill",
    label: "Seed Drill (बीज ड्रिल मशीन)",
    minWeight: 100,
    maxWeight: 300,
  },
  {
    value: "rotavator",
    label: "Rotavator (रोटावेटर)",
    minWeight: 250,
    maxWeight: 450,
  },
  {
    value: "cultivator",
    label: "Cultivator (कल्टीवेटर)",
    minWeight: 100,
    maxWeight: 250,
  },
  {
    value: "sprayer",
    label: "Sprayer (स्प्रेयर)",
    minWeight: 10,
    maxWeight: 20,
  },
  {
    value: "thresher",
    label: "Thresher (थ्रेशर)",
    minWeight: 200,
    maxWeight: 600,
  },
  {
    value: "combine-harvester",
    label: "Combine Harvester (कंबाइन हार्वेस्टर)",
    minWeight: 8000,
    maxWeight: 15000,
  },
  {
    value: "water-pump",
    label: "Water Pump (पानी का पंप)",
    minWeight: 15,
    maxWeight: 60,
  },
];

document.addEventListener("DOMContentLoaded", () => {
  setYear();

  const page = document.body.dataset.page;
  if (page === "home" || page === "services" || page === "contact" || page === "privacy-policy") {
    initPublicPages();
  }
  if (page === "admin-login") {
    initAdminLogin();
  }
  if (page === "admin" || page === "admin-dashboard") {
    initAdminDashboard();
  }

  // Check for admin login modal trigger after a short delay
  setTimeout(checkAdminLoginModal, 100);
  
  // Initialize admin login modal for all pages (keeping for potential future use)
  // initAdminLoginModal();
});


function setYear() {
  const yearNode = document.getElementById("year");
  if (yearNode) {
    yearNode.textContent = String(new Date().getFullYear());
  }
}

function checkAdminLoginModal() {
  // This function is no longer needed since we use direct /admin route
  // Keeping for backward compatibility if needed
}

function showAdminLoginModal() {
  // Modal functionality removed - now using direct /admin-login.html page
  window.location.href = "/admin-login.html";
}

function hideAdminLoginModal() {
  // Modal functionality removed
}

function initAdminLoginModal() {
  // Modal functionality removed - now using direct /admin page
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    credentials: "include",
    ...options,
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch (error) {
    payload = {};
  }

  if (!response.ok) {
    throw new Error(payload.error || "Request failed");
  }

  return payload;
}

async function initPublicPages() {
  initSiteNavbar();
  initContactEnquiryForm();
  initQuickContactForm();
  initServiceOrderForms();
  initAgricultureMachineOptions();
  initCart();
  initScrollReveal();
  initStatCounters();

  try {
    const data = await fetchJson(api.publicData, { method: "GET" });
    fillBusinessContent(data.business || {});
    fillServiceContent(data.services || {});
    fillPublicGalleries(data.galleries || {});
    hideDisabledServiceBoxes(data.services || {});
  } catch (error) {
    console.error(error);
  }
}

function initScrollReveal() {
  const revealNodes = document.querySelectorAll("[data-reveal]");
  if (!revealNodes.length) {
    return;
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    revealNodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.18,
      rootMargin: "0px 0px -40px 0px",
    }
  );

  revealNodes.forEach((node, index) => {
    node.style.setProperty("--reveal-delay", `${Math.min(index * 70, 280)}ms`);
    observer.observe(node);
  });
}

function initStatCounters() {
  const counterNodes = document.querySelectorAll("[data-counter-target]");
  if (!counterNodes.length) {
    return;
  }

  const formatCounterValue = (value) => {
    if (value >= 1000) {
      return `${value}+`;
    }
    return `${value}+`;
  };

  const animateCounter = (node) => {
    const target = Number(node.dataset.counterTarget || "0");
    if (!Number.isFinite(target) || target <= 0) {
      node.textContent = "0";
      return;
    }

    const duration = 1200;
    const start = performance.now();

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(target * eased);
      node.textContent = formatCounterValue(current);

      if (progress < 1) {
        window.requestAnimationFrame(tick);
      } else {
        node.textContent = formatCounterValue(target);
      }
    };

    window.requestAnimationFrame(tick);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        animateCounter(entry.target);
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.4,
    }
  );

  counterNodes.forEach((node) => {
    node.textContent = "0";
    observer.observe(node);
  });
}

function initSiteNavbar() {
  const toggle = document.getElementById("navbar-toggle");
  const menu = document.getElementById("site-navbar-menu");

  if (!toggle || !menu) {
    return;
  }

  const closeMenu = () => {
    menu.classList.remove("is-open");
    toggle.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  };

  toggle.addEventListener("click", () => {
    const isOpen = menu.classList.toggle("is-open");
    toggle.classList.toggle("is-open", isOpen);
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  menu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 760) {
        closeMenu();
      }
    });
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 760) {
      closeMenu();
    }
  });
}

function fillBusinessContent(business) {
  setText("welcome-text", business.welcomeText);
  setText("footer-about", business.aboutText);
  setText("footer-phone", business.phone);
  setText("footer-address", business.address);
  setText("footer-email", business.email);
  setText("contact-phone", business.phone);
  setText("contact-address", business.address);
  setText("contact-email", business.email);
  // Quick contact section
  setText("contact-phone-quick", business.phone);
  setText("contact-address-quick", business.address);
  setText("contact-email-quick", business.email);
  setLink("contact-phone-quick", `tel:${business.phone}`);
  setLink("contact-email-quick", `mailto:${business.email}`);
  setLink("instagram-link", business.instagram);
  setLink("facebook-link", business.facebook);
  setLink("contact-instagram", business.instagram);
  setLink("contact-facebook", business.facebook);
  setLink("footer-instagram", business.instagram);
  setLink("footer-facebook", business.facebook);
  setConditionalLink("footer-whatsapp", buildWhatsAppUrl(business.whatsapp || business.phone));
  setConditionalLink("footer-youtube", business.youtube);
}

function fillServiceContent(services) {
  const descriptions = document.querySelectorAll("[data-service-desc]");
  descriptions.forEach((node) => {
    const key = node.dataset.serviceDesc;
    const service = services[key];
    // Handle both old string format and new object format
    const description = typeof service === 'string' ? service : (service?.description || "");
    node.textContent = description;
  });

  // Hide/show services based on enabled status
  const serviceSections = ["agriculture", "doors", "chogaths"];
  const serviceStates = getServiceStates();
  
  serviceSections.forEach((serviceKey) => {
    const section = document.getElementById(serviceKey);
    if (section) {
      const service = services[serviceKey];
      // Check localStorage first, then fall back to service data
      let isEnabled = serviceStates[serviceKey];
      
      if (isEnabled === undefined) {
        // Fall back to service data
        isEnabled = typeof service === 'string' ? true : (service?.enabled !== false);
      }
      
      if (!isEnabled) {
        section.classList.add("hidden");
      } else {
        section.classList.remove("hidden");
      }
    }
  });
}

function hideDisabledServiceBoxes(services) {
  const serviceBoxes = document.querySelectorAll(".service-box");
  const serviceStates = getServiceStates();
  const serviceKeys = ["agriculture", "doors", "chogaths"];

  serviceBoxes.forEach((box, index) => {
    if (index >= serviceKeys.length) {
      return;
    }

    const serviceKey = serviceKeys[index];
    const service = services[serviceKey];
    let isEnabled = serviceStates[serviceKey];

    if (isEnabled === undefined) {
      isEnabled = typeof service === 'string' ? true : (service?.enabled !== false);
    }

    if (!isEnabled) {
      box.style.display = "none";
    } else {
      box.style.display = "block";
    }
  });
}

function fillPublicGalleries(galleries) {
  renderGallery(
    document.getElementById("admin-photos-gallery"),
    galleries.admin || [],
    galleryPlaceholders.admin
  );
  renderGallery(
    document.getElementById("agriculture-gallery"),
    galleries.agriculture || [],
    galleryPlaceholders.agriculture
  );
  renderGallery(
    document.getElementById("doors-gallery"),
    galleries.doors || [],
    galleryPlaceholders.doors
  );
  renderGallery(
    document.getElementById("chogaths-gallery"),
    galleries.chogaths || [],
    galleryPlaceholders.chogaths
  );
}

async function initAdminLogin() {
  try {
    const session = await fetchJson(api.adminSession, { method: "GET" });
    if (session.authenticated) {
      window.location.href = "/admin.html";
      return;
    }
  } catch (error) {
    console.error(error);
  }

  const form = document.getElementById("login-form");
  const message = document.getElementById("login-message");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "Logging in...";

    const payload = {
      username: form.username.value,
      password: form.password.value,
    };

    try {
      await fetchJson(api.login, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      message.textContent = "Login successful. Redirecting...";
      window.location.href = "/admin.html";
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

async function initAdminDashboard() {
  const session = await fetchJson(api.adminSession, { method: "GET" }).catch(() => ({
    authenticated: false,
  }));

  if (!session.authenticated) {
    window.location.href = "/admin-login.html";
    return;
  }

  setText("admin-session-user", session.username || "Admin");
  bindLogout();
  bindForms();
  bindUploaders();
  bindEnquiryRefresh();
  bindOrderRefresh();
  bindDashboardFilters();
  await loadDashboardData();
}

function bindLogout() {
  const logoutBtn = document.getElementById("logout-btn");
  if (!logoutBtn) {
    return;
  }

  logoutBtn.addEventListener("click", async () => {
    await fetchJson(api.logout, { method: "POST", body: JSON.stringify({}) }).catch(() => null);
    window.location.href = "/admin-login.html";
  });
}

function bindForms() {
  const businessForm = document.getElementById("business-info-form");
  const serviceForm = document.getElementById("service-desc-form");
  const businessMessage = document.getElementById("business-info-message");
  const serviceMessage = document.getElementById("service-desc-message");

  if (businessForm) {
    businessForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      businessMessage.textContent = "Saving business info...";

      const payload = {
        aboutText: document.getElementById("aboutText").value.trim(),
        welcomeText: document.getElementById("welcomeText").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        whatsapp: document.getElementById("whatsapp").value.trim(),
        address: document.getElementById("address").value.trim(),
        email: document.getElementById("email").value.trim(),
        instagram: document.getElementById("instagram").value.trim(),
        facebook: document.getElementById("facebook").value.trim(),
      };

      try {
        await fetchJson(api.businessInfo, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        businessMessage.textContent = "Business information saved.";
      } catch (error) {
        businessMessage.textContent = error.message;
      }
    });
  }

  if (serviceForm) {
    serviceForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      serviceMessage.textContent = "Saving service descriptions...";

      const payload = {
        agriculture: document.getElementById("descAgriculture").value.trim(),
        doors: document.getElementById("descDoors").value.trim(),
        chogaths: document.getElementById("descChogaths").value.trim(),
      };

      try {
        await fetchJson(api.serviceDescriptions, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        serviceMessage.textContent = "Service descriptions saved.";
      } catch (error) {
        serviceMessage.textContent = error.message;
      }
    });
  }

  bindServiceToggles();
}

function bindServiceToggles() {
  const toggleButtons = document.querySelectorAll(".toggle-switch");
  const saveButton = document.getElementById("save-service-toggles");
  const message = document.getElementById("service-toggle-message");

  // Initialize toggle states from localStorage
  const serviceStates = getServiceStates();
  toggleButtons.forEach((btn) => {
    const service = btn.dataset.service;
    if (service && serviceStates[service] !== undefined) {
      const isEnabled = serviceStates[service];
      btn.classList.toggle("active", isEnabled);
    }
  });

  // Toggle click handlers
  toggleButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.classList.toggle("active");
    });
  });

  // Save button handler
  if (saveButton && message) {
    saveButton.addEventListener("click", async () => {
      message.textContent = "Saving service settings...";

      const newStates = {};
      toggleButtons.forEach((btn) => {
        const service = btn.dataset.service;
        if (service) {
          newStates[service] = btn.classList.contains("active");
        }
      });

      try {
        // Save to server via serviceDescriptions API (we'll update the backend to handle this)
        // For now, save locally in localStorage for frontend persistence
        saveServiceStates(newStates);
        message.textContent = "Service settings saved successfully!";
        
        // Reload the page to reflect changes
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } catch (error) {
        message.textContent = error.message;
      }
    });
  }
}

function getServiceStates() {
  try {
    const states = localStorage.getItem("mrw_service_states");
    return states ? JSON.parse(states) : {};
  } catch (error) {
    return {};
  }
}

function saveServiceStates(states) {
  localStorage.setItem("mrw_service_states", JSON.stringify(states));
}

function bindUploaders() {
  const uploadTargets = [
    { inputId: "adminPhotosInput", category: "admin", manageId: "adminPhotosManage" },
    { inputId: "agricultureInput", category: "agriculture", manageId: "agricultureManage" },
    { inputId: "doorsInput", category: "doors", manageId: "doorsManage" },
    { inputId: "chogathsInput", category: "chogaths", manageId: "chogathsManage" },
  ];

  uploadTargets.forEach(({ inputId, category }) => {
    const input = document.getElementById(inputId);
    if (!input) {
      return;
    }

    input.addEventListener("change", async () => {
      if (!input.files || input.files.length === 0) {
        return;
      }

      try {
        const files = await Promise.all(Array.from(input.files).map(fileToPayload));
        await fetchJson(api.photos(category), {
          method: "POST",
          body: JSON.stringify({ files }),
        });
        input.value = "";
        await loadDashboardData();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

function bindEnquiryRefresh() {
  const refreshBtn = document.getElementById("refresh-enquiries-btn");
  if (!refreshBtn) {
    return;
  }

  refreshBtn.addEventListener("click", async () => {
    const data = await fetchJson(api.adminEnquiries, { method: "GET" });
    renderEnquiries(data.enquiries || []);
  });
}

function bindOrderRefresh() {
  const refreshBtn = document.getElementById("refresh-orders-btn");
  if (!refreshBtn) {
    return;
  }

  refreshBtn.addEventListener("click", async () => {
    const data = await fetchJson(api.adminOrders, { method: "GET" });
    renderOrders(data.orders || []);
  });
}

async function loadDashboardData() {
  try {
    const data = await fetchJson(api.adminDashboard, { method: "GET" });
    populateDashboardForms(data);
    populateDashboardOverview(data);
    renderManageGalleries(data.galleries || {});
    dashboardState.enquiries = data.enquiries || [];
    dashboardState.orders = data.orders || [];
    applyDashboardFilters();
  } catch (error) {
    alert(error.message);
  }
}

function populateDashboardForms(data) {
  const business = data.business || {};
  const services = data.services || {};

  setValue("aboutText", business.aboutText);
  setValue("welcomeText", business.welcomeText);
  setValue("phone", business.phone);
  setValue("whatsapp", business.whatsapp || business.phone);
  setValue("address", business.address);
  setValue("email", business.email);
  setValue("instagram", business.instagram);
  setValue("facebook", business.facebook);
  
  // Handle both old string format and new object format for services
  const agricultureService = services.agriculture;
  const doorsService = services.doors;
  const chogathsService = services.chogaths;
  
  setValue("descAgriculture", typeof agricultureService === 'string' ? agricultureService : (agricultureService?.description || ""));
  setValue("descDoors", typeof doorsService === 'string' ? doorsService : (doorsService?.description || ""));
  setValue("descChogaths", typeof chogathsService === 'string' ? chogathsService : (chogathsService?.description || ""));
}

function populateDashboardOverview(data) {
  const galleries = data.galleries || {};
  const services = data.services || {};
  const serviceKeys = ["agriculture", "doors", "chogaths"];
  const activeServices = serviceKeys.filter((key) => {
    const service = services[key];
    return typeof service === "string" ? true : service?.enabled !== false;
  }).length;

  setText("overview-active-services", String(activeServices));
  setText("overview-enquiries", String((data.enquiries || []).length));
  setText("overview-orders", String((data.orders || []).length));
  setText(
    "overview-photos",
    String(
      ["admin", "agriculture", "doors", "chogaths"].reduce(
        (total, key) => total + ((galleries[key] || []).length),
        0
      )
    )
  );
}

function renderManageGalleries(galleries) {
  const targets = [
    { manageId: "adminPhotosManage", category: "admin" },
    { manageId: "agricultureManage", category: "agriculture" },
    { manageId: "doorsManage", category: "doors" },
    { manageId: "chogathsManage", category: "chogaths" },
  ];

  targets.forEach(({ manageId, category }) => {
    const container = document.getElementById(manageId);
    renderGallery(
      container,
      galleries[category] || [],
      galleryPlaceholders[category],
      async (photoId) => {
        await fetchJson(api.photoItem(category, photoId), { method: "DELETE" });
        await loadDashboardData();
      }
    );
  });
}

function renderEnquiries(enquiries) {
  const container = document.getElementById("enquiriesList");
  if (!container) {
    return;
  }

  if (!enquiries.length) {
    container.innerHTML = '<div class="placeholder-card">No enquiries yet.</div>';
    return;
  }

  container.innerHTML = enquiries
    .map(
      (item) => `
        <article class="enquiry-card">
          <h3>${escapeHtml(item.name)}</h3>
          <div class="enquiry-meta">
            <span>Phone: ${escapeHtml(item.phone)}</span>
            <span>Email: ${escapeHtml(item.email || "Not provided")}</span>
            <span>Service: ${escapeHtml(item.service)}</span>
            <span>Time: ${escapeHtml(formatDate(item.createdAt))}</span>
          </div>
          <p class="enquiry-message">${escapeHtml(item.message)}</p>
          <button class="remove-btn enquiry-remove-btn" type="button" data-enquiry-id="${escapeHtml(item.id)}">Delete</button>
        </article>
      `
    )
    .join("");

  container.querySelectorAll("[data-enquiry-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const enquiryId = button.dataset.enquiryId;
      const confirmed = window.confirm("Delete this enquiry?");
      if (!confirmed) {
        return;
      }
      await fetchJson(api.enquiryItem(enquiryId), { method: "DELETE" });
      await loadDashboardData();
    });
  });
}

function renderOrders(orders) {
  const container = document.getElementById("ordersList");
  if (!container) {
    return;
  }

  if (!orders.length) {
    container.innerHTML = '<div class="placeholder-card">No orders yet.</div>';
    return;
  }

  container.innerHTML = orders
    .map((item) => {
      const fields = Object.entries(item.fields || {})
        .filter(([, value]) => value)
        .map(([key, value]) => `<span>${escapeHtml(prettyFieldLabel(key))}: ${escapeHtml(value)}</span>`)
        .join("");

      return `
        <article class="enquiry-card">
          <h3>${escapeHtml(item.label || item.service || "Order")}</h3>
          <div class="enquiry-meta">
            <span>Customer: ${escapeHtml(item.fields?.customerName || "-")}</span>
            <span>Phone: ${escapeHtml(item.fields?.phone || "-")}</span>
            <span>Time: ${escapeHtml(formatDate(item.createdAt))}</span>
          </div>
          <div class="order-fields">${fields}</div>
          <button class="remove-btn order-remove-btn" type="button" data-order-id="${escapeHtml(item.id)}">Delete</button>
        </article>
      `;
    })
    .join("");

  container.querySelectorAll("[data-order-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const orderId = button.dataset.orderId;
      const confirmed = window.confirm("Delete this order?");
      if (!confirmed) {
        return;
      }
      await fetchJson(api.orderItem(orderId), { method: "DELETE" });
      await loadDashboardData();
    });
  });
}

function bindDashboardFilters() {
  const filterIds = [
    "enquiry-search",
    "enquiry-service-filter",
    "order-search",
    "order-service-filter",
  ];

  filterIds.forEach((id) => {
    const node = document.getElementById(id);
    if (!node || node.dataset.bound === "true") {
      return;
    }

    node.dataset.bound = "true";
    node.addEventListener("input", applyDashboardFilters);
    node.addEventListener("change", applyDashboardFilters);
  });
}

function applyDashboardFilters() {
  renderEnquiries(filterEnquiries(dashboardState.enquiries));
  renderOrders(filterOrders(dashboardState.orders));
}

function filterEnquiries(items) {
  const search = (document.getElementById("enquiry-search")?.value || "").trim().toLowerCase();
  const service = (document.getElementById("enquiry-service-filter")?.value || "").trim().toLowerCase();

  return items.filter((item) => {
    const haystack = [item.name, item.phone, item.email, item.service, item.message]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const matchesSearch = !search || haystack.includes(search);
    const matchesService = !service || String(item.service || "").toLowerCase() === service;
    return matchesSearch && matchesService;
  });
}

function filterOrders(items) {
  const search = (document.getElementById("order-search")?.value || "").trim().toLowerCase();
  const service = (document.getElementById("order-service-filter")?.value || "").trim().toLowerCase();

  return items.filter((item) => {
    const fields = item.fields || {};
    const haystack = [
      item.label,
      item.service,
      fields.customerName,
      fields.phone,
      fields.companyName,
      fields.machineName,
      fields.comment,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const matchesSearch = !search || haystack.includes(search);
    const matchesService = !service || String(item.service || "").toLowerCase() === service;
    return matchesSearch && matchesService;
  });
}

function initContactEnquiryForm() {
  const form = document.getElementById("contact-enquiry-form");
  const message = document.getElementById("contact-enquiry-message");

  if (!form || !message || form.dataset.bound === "true") {
    return;
  }

  form.dataset.bound = "true";
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "Submitting enquiry...";

    const payload = {
      name: form.name.value.trim(),
      phone: form.phone.value.trim(),
      email: form.email.value.trim(),
      service: form.service.value.trim(),
      message: form.message.value.trim(),
    };

    try {
      await fetchJson(api.enquiries, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      form.reset();
      message.textContent = "Enquiry sent successfully. We will contact you soon.";
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

function initQuickContactForm() {
  const form = document.getElementById("quick-contact-form");
  const message = document.getElementById("quick-contact-message");

  if (!form || !message || form.dataset.bound === "true") {
    return;
  }

  form.dataset.bound = "true";
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "Sending...";

    const payload = {
      name: form.querySelector('input[name="name"]').value.trim(),
      phone: form.querySelector('input[name="phone"]').value.trim(),
      email: "",
      service: "Quick Enquiry",
      message: form.querySelector('textarea[name="message"]').value.trim(),
    };

    try {
      await fetchJson(api.enquiries, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      form.reset();
      message.textContent = "Message sent successfully!";
      setTimeout(() => {
        message.textContent = "";
      }, 3000);
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

function initServiceOrderForms() {
  document.querySelectorAll(".service-order-form").forEach((form) => {
    if (form.dataset.bound === "true") {
      return;
    }

    form.dataset.bound = "true";
    const syncCustomSizeState = initChogathCustomSizeFields(form);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const service = form.dataset.orderService;
      const message = document.querySelector(`[data-order-message="${service}"]`);
      const submitBtn = form.querySelector('button[type="submit"]');
      const originalSubmitText = submitBtn ? submitBtn.textContent : "Submit Order";
      if (message) {
        renderOrderFeedback(message, {
          type: "loading",
          text: "Submitting your order...",
        });
      }
      setButtonLoading(submitBtn, true, "Submitting...");

      const payload = {
        service,
        fields: collectOrderFields(service, form),
      };

      try {
        const response = await fetchJson(api.orders, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        form.reset();
        syncCustomSizeState();
        if (message) {
          renderOrderFeedback(message, {
            type: "success",
            text: "Order submitted successfully!",
            whatsappUrl: response.whatsappUrl,
            orderId: response.order?.id,
            submittedAt: response.order?.createdAt,
          });
        }
      } catch (error) {
        if (message) {
          renderOrderFeedback(message, {
            type: "error",
            text: error.message || "Something went wrong. Please try again.",
          });
        }
      } finally {
        setButtonLoading(submitBtn, false, originalSubmitText);
      }
    });

    // Add to Cart button handler
    const addToCartBtn = form.querySelector(".add-to-cart-order");
    if (addToCartBtn) {
      addToCartBtn.addEventListener("click", (event) => {
        event.preventDefault();
        const service = form.dataset.orderService;
        const fields = collectOrderFields(service, form);
        
        // Create a readable cart item name and details
        const serviceNames = {
          agriculture: "Agriculture Machine Repair",
          doors: "Main Door Repair",
          chogaths: "Chogath Repair"
        };
        
        const itemName = serviceNames[service] || service;
        const details = formatOrderDetails(fields);
        
        addToCart(itemName, details, service, fields);
        form.reset();
        syncCustomSizeState();
        
        // Show success message
        const message = document.querySelector(`[data-order-message="${service}"]`);
        if (message) {
          renderOrderFeedback(message, {
            type: "success",
            text: "Added to cart successfully!",
          });
          setTimeout(() => {
            message.innerHTML = "";
            message.className = "message-text";
          }, 3000);
        }
      });
    }
  });
}

function setButtonLoading(button, isLoading, loadingText = "Submitting...") {
  if (!button) {
    return;
  }

  if (isLoading) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    button.textContent = loadingText;
    button.disabled = true;
    button.classList.add("is-loading");
    return;
  }

  button.textContent = loadingText || button.dataset.originalText || button.textContent;
  button.disabled = false;
  button.classList.remove("is-loading");
  delete button.dataset.originalText;
}

function renderOrderFeedback(container, config) {
  if (!container) {
    return;
  }

  const type = config.type || "success";
  const text = escapeHtml(config.text || "");
  const orderMeta = [];
  if (config.orderId) {
    orderMeta.push(`Order ID: ${escapeHtml(config.orderId)}`);
  }
  if (config.submittedAt) {
    orderMeta.push(`Submitted: ${escapeHtml(formatDate(config.submittedAt))}`);
  }
  const whatsappButton = config.whatsappUrl
    ? `<button type="button" class="btn-secondary whatsapp-order-btn" data-whatsapp-url="${escapeHtml(config.whatsappUrl)}">Send via WhatsApp</button>`
    : "";
  const metaMarkup = orderMeta.length
    ? `<div class="order-feedback-meta">${orderMeta.map((item) => `<span>${item}</span>`).join("")}</div>`
    : "";

  container.className = `message-text order-feedback order-feedback-${type}`;
  container.innerHTML = `
    <div class="order-feedback-content">
      <div class="order-feedback-copy">
        <span class="order-feedback-text">${text}</span>
        ${metaMarkup}
      </div>
      ${whatsappButton}
    </div>
  `;

  const whatsappBtn = container.querySelector("[data-whatsapp-url]");
  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", () => {
      window.open(whatsappBtn.dataset.whatsappUrl, "_blank", "noopener");
    });
  }
}

function initChogathCustomSizeFields(form) {
  if (form.dataset.orderService !== "chogaths") {
    return () => {};
  }

  const sizeSelect = form.querySelector('[name="sizeOption"]');
  const customSizeFields = document.getElementById("chogathCustomSizeFields");
  const widthInput = form.querySelector('[name="customWidth"]');
  const heightInput = form.querySelector('[name="customHeight"]');
  const widthUnitSelect = form.querySelector('[name="customWidthUnit"]');
  const heightUnitSelect = form.querySelector('[name="customHeightUnit"]');
  const hiddenCustomSize = form.querySelector('[name="customSize"]');
  const preview = document.getElementById("chogathCustomSizePreview");

  if (!sizeSelect || !customSizeFields || !widthInput || !heightInput || !widthUnitSelect || !heightUnitSelect || !hiddenCustomSize || !preview) {
    return () => {};
  }

  const unitLabel = (value) => {
    if (value === "in") {
      return "inch";
    }
    return "ft";
  };

  const syncState = () => {
    const useCustomSize = sizeSelect.value === "Your Size";
    customSizeFields.classList.toggle("is-hidden", !useCustomSize);
    widthInput.required = useCustomSize;
    heightInput.required = useCustomSize;

    if (!useCustomSize) {
      widthInput.value = "";
      heightInput.value = "";
      widthUnitSelect.value = "ft";
      heightUnitSelect.value = "ft";
      hiddenCustomSize.value = "";
      preview.textContent = "";
      return;
    }

    const width = widthInput.value.trim();
    const height = heightInput.value.trim();
    const widthUnit = unitLabel(widthUnitSelect.value);
    const heightUnit = unitLabel(heightUnitSelect.value);

    if (width && height) {
      hiddenCustomSize.value = `${width} ${widthUnit} x ${height} ${heightUnit}`;
      preview.textContent = `${width} ${widthUnit} x ${height} ${heightUnit} (This is according outer side)`;
      return;
    }

    hiddenCustomSize.value = "";
    preview.textContent = "Enter width and height. (This is according outer side)";
  };

  sizeSelect.addEventListener("change", syncState);
  widthInput.addEventListener("input", syncState);
  heightInput.addEventListener("input", syncState);
  widthUnitSelect.addEventListener("change", syncState);
  heightUnitSelect.addEventListener("change", syncState);
  syncState();
  return syncState;
}

function initAgricultureMachineOptions() {
  const machineSelect = document.getElementById("agriMachineName");
  const weightSelect = document.getElementById("agriWeight");

  if (!machineSelect || !weightSelect) {
    return;
  }

  machineSelect.innerHTML = '<option value="">Select machine</option>';

  agricultureMachineCatalog.forEach((machine) => {
    const option = document.createElement("option");
    option.value = machine.label;
    option.textContent = machine.label;
    option.dataset.machineKey = machine.value;
    machineSelect.appendChild(option);
  });

  const updateWeights = () => {
    const selectedMachine = agricultureMachineCatalog.find(
      (machine) => machine.label === machineSelect.value
    );

    renderAgricultureWeightOptions(weightSelect, selectedMachine);
  };

  machineSelect.addEventListener("change", updateWeights);
  renderAgricultureWeightOptions(weightSelect, null);
}

function renderAgricultureWeightOptions(weightSelect, machine) {
  weightSelect.innerHTML = "";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = machine ? "Select estimated weight" : "Select machine first";
  weightSelect.appendChild(placeholder);

  if (!machine) {
    return;
  }

  buildAgricultureWeightRanges(machine).forEach((range) => {
    const option = document.createElement("option");
    option.value = range;
    option.textContent = range;
    weightSelect.appendChild(option);
  });
}

function buildAgricultureWeightRanges(machine) {
  return ["Standard", "Medium", "Heavy", "Extra Heavy"];
}

function collectOrderFields(service, form) {
  if (service === "agriculture") {
    return {
      machineName: form.machineName.value.trim(),
      weight: form.weight.value.trim(),
      color: form.color.value.trim(),
      colorSuggestion: form.colorSuggestion.value.trim(),
      comment: form.comment.value.trim(),
      customerName: form.customerName.value.trim(),
      phone: form.phone.value.trim(),
    };
  }

  if (service === "doors") {
    return {
      doorType: form.doorType.value.trim(),
      size: form.size.value.trim(),
      weight: form.weight.value.trim(),
      color: form.color.value.trim(),
      colorSuggestion: form.colorSuggestion.value.trim(),
      customerName: form.customerName.value.trim(),
      phone: form.phone.value.trim(),
    };
  }

  return {
    sizeOption: form.sizeOption.value.trim(),
      customSize: form.customSize.value.trim(),
      companyName: form.companyName.value.trim(),
      weight: form.weight.value.trim(),
      customerName: form.customerName.value.trim(),
      phone: form.phone.value.trim(),
    };
}

function formatOrderDetails(fields) {
  const details = [];
  
  if (fields.customerName) details.push(`Name: ${fields.customerName}`);
  if (fields.phone) details.push(`Phone: ${fields.phone}`);
  if (fields.machineName) details.push(`Machine: ${fields.machineName}`);
  if (fields.weight) details.push(`Weight: ${fields.weight} kg`);
  if (fields.doorType) details.push(`Door Type: ${fields.doorType}`);
  if (fields.size) details.push(`Door Size: ${fields.size}`);
  if (fields.sizeOption) details.push(`Size Option: ${fields.sizeOption}`);
  if (fields.customSize) details.push(`Custom Size: ${fields.customSize}`);
  if (fields.companyName) details.push(`Company: ${fields.companyName}`);
  if (fields.color) details.push(`Color: ${fields.color}`);
  if (fields.colorSuggestion) details.push(`Color Suggestion: ${fields.colorSuggestion}`);
  if (fields.comment) details.push(`Comment: ${fields.comment}`);
  
  return details.join(", ");
}

function renderGallery(container, items, emptyText, onRemove) {
  if (!container) {
    return;
  }

  if (!items.length) {
    container.innerHTML = `<div class="placeholder-card">${emptyText}</div>`;
    return;
  }

  container.innerHTML = items
    .map((item) => {
      const removeButton = onRemove
        ? `<button class="remove-btn" type="button" data-photo-id="${item.id}">Remove</button>`
        : "";
      const wrapperClass = onRemove ? "manage-card" : "photo-card";
      return `
        <div class="${wrapperClass}">
          ${removeButton}
          <img src="${item.url}" alt="${escapeHtml(item.filename || "Image")}">
        </div>
      `;
    })
    .join("");

  if (onRemove) {
    container.querySelectorAll("[data-photo-id]").forEach((button) => {
      button.addEventListener("click", async () => {
        const photoId = button.dataset.photoId;
        await onRemove(photoId);
      });
    });
  }
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node && value) {
    node.textContent = value;
  }
}

function setLink(id, href) {
  const node = document.getElementById(id);
  if (node && href) {
    node.href = href;
  }
}

function setConditionalLink(id, href) {
  const node = document.getElementById(id);
  if (!node) {
    return;
  }

  if (href) {
    node.href = href;
    node.classList.remove("is-hidden");
    return;
  }

  node.classList.add("is-hidden");
}

function setValue(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.value = value || "";
  }
}

function buildWhatsAppUrl(value) {
  const cleaned = String(value || "").replace(/[^\d]/g, "");
  if (!cleaned) {
    return "";
  }

  return `https://wa.me/${cleaned}`;
}

function fileToPayload(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ name: file.name, dataUrl: reader.result });
    reader.onerror = () => reject(new Error(`Unable to read ${file.name}`));
    reader.readAsDataURL(file);
  });
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value || "";
  }
  return date.toLocaleString();
}

function prettyFieldLabel(key) {
  const labels = {
    machineName: "Machine Name",
    weight: "Weight",
    color: "Colour",
    colorSuggestion: "Colour Mix Suggestion",
    comment: "Comment and Suggestion",
    customerName: "Customer Name",
    phone: "Phone",
    doorType: "Door Type",
    size: "Size",
    sizeOption: "Chogath Size",
    customSize: "Your Size",
    companyName: "Company Name",
  };
  return labels[key] || key;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// ===== CART FEATURE FUNCTIONS =====
const CART_STORAGE_KEY = "mrw_cart";

function initCart() {
  setupCartElements();
  loadCart();
  updateCartUI();
}

function setupCartElements() {
  // Cart modal
  const modal = document.getElementById("cart-modal");
  if (modal) {
    const closeBtn = document.getElementById("close-cart-btn");
    const checkoutBtn = document.getElementById("checkout-btn");
    
    if (closeBtn) {
      closeBtn.addEventListener("click", () => modal.classList.remove("show"));
    }
    
    if (checkoutBtn) {
      checkoutBtn.addEventListener("click", handleCheckoutFlow);
    }
  }

  // Cart open buttons
  const cartLinks = document.querySelectorAll(".cart-link, #open-cart-btn, #view-cart-link");
  cartLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      openCart();
    });
  });

  // Add to cart buttons (if any exist)
  document.querySelectorAll(".add-to-cart-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const itemName = btn.dataset.itemName;
      const itemDetails = btn.dataset.itemDetails || "";
      if (itemName) {
        addToCart(itemName, itemDetails);
      }
    });
  });
}

function getCart() {
  try {
    const cart = localStorage.getItem(CART_STORAGE_KEY);
    return cart ? JSON.parse(cart) : [];
  } catch (error) {
    console.error("Error loading cart:", error);
    return [];
  }
}

function saveCart(cart) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  } catch (error) {
    console.error("Error saving cart:", error);
  }
}

function loadCart() {
  return getCart();
}

function addToCart(name, details = "", service = "", fields = {}) {
  const cart = getCart();
  const id = Date.now().toString();
  cart.push({
    id,
    name,
    details,
    service,
    fields,
    addedAt: new Date().toLocaleString(),
  });
  saveCart(cart);
  updateCartUI();
  showNotification("Added to cart!");
}

function removeFromCart(id) {
  const cart = getCart();
  const filtered = cart.filter((item) => item.id !== id);
  saveCart(filtered);
  updateCartUI();
}

function clearCart() {
  saveCart([]);
  updateCartUI();
}

function updateCartUI() {
  const cart = getCart();
  const countBadges = document.querySelectorAll("[data-cart-count], #cart-count-sidebar");
  const totalItems = document.getElementById("cart-total-items");
  
  countBadges.forEach((badge) => {
    badge.textContent = cart.length;
  });
  
  if (totalItems) {
    totalItems.textContent = cart.length;
  }

  const checkoutBtn = document.getElementById("checkout-btn");
  if (checkoutBtn) {
    checkoutBtn.disabled = cart.length === 0;
  }
}

function renderCartModal() {
  const cart = getCart();
  const container = document.getElementById("cart-items-container");
  
  if (!container) {
    return;
  }

  if (cart.length === 0) {
    container.innerHTML = '<p class="empty-cart-msg">Your cart is empty. Start adding services!</p>';
    return;
  }

  container.innerHTML = cart
    .map(
      (item) => `
        <div class="cart-item">
          <div class="cart-item-info">
            <div class="cart-item-name">${escapeHtml(item.name)}</div>
            ${item.details ? `<div class="cart-item-details">${escapeHtml(item.details)}</div>` : ""}
            <div class="cart-item-details" style="font-size: 0.75rem; color: #999;">Added: ${item.addedAt}</div>
          </div>
          <button class="remove-cart-item" data-cart-item-id="${item.id}">Remove</button>
        </div>
      `
    )
    .join("");

  // Attach remove event listeners
  container.querySelectorAll("[data-cart-item-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      removeFromCart(btn.dataset.cartItemId);
      renderCartModal();
    });
  });
}

function openCart() {
  const modal = document.getElementById("cart-modal");
  if (!modal) {
    return;
  }

  renderCartModal();
  modal.classList.add("show");
}

async function handleCheckoutFlow() {
  const cart = getCart();
  if (cart.length === 0) {
    alert("Your cart is empty!");
    return;
  }

  const checkoutBtn = document.getElementById("checkout-btn");
  const container = document.getElementById("cart-items-container");
  const originalText = checkoutBtn ? checkoutBtn.textContent : "Place Order";
  setButtonLoading(checkoutBtn, true, "Submitting orders...");

  try {
    const submittedOrders = [];
    for (const item of cart) {
      if (item.service && item.fields) {
        const payload = {
          service: item.service,
          fields: item.fields,
        };

        const response = await fetchJson(api.orders, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        submittedOrders.push(response);
      }
    }

    clearCart();

    const whatsappUrl = submittedOrders[0]?.whatsappUrl || "";
    if (container) {
      container.innerHTML = `
        <div class="order-success-message">
          <div class="success-icon">OK</div>
          <h3>Order submitted successfully!</h3>
          <p>Your order has been saved successfully.</p>
          <p class="order-success-meta">Order ID: ${escapeHtml(submittedOrders[0]?.order?.id || "-")}</p>
          <p class="order-success-meta">Submitted: ${escapeHtml(submittedOrders[0]?.order?.createdAt ? formatDate(submittedOrders[0].order.createdAt) : "-")}</p>
          ${whatsappUrl ? `<button class="btn-secondary reorder-btn" id="cart-whatsapp-btn" data-whatsapp-url="${escapeHtml(whatsappUrl)}">Send via WhatsApp</button>` : ""}
        </div>
      `;
    }

    const whatsappBtn = document.getElementById("cart-whatsapp-btn");
    if (whatsappBtn) {
      whatsappBtn.addEventListener("click", () => {
        window.open(whatsappBtn.dataset.whatsappUrl, "_blank", "noopener");
      });
    }
  } catch (error) {
    console.error("Error submitting orders:", error);
    if (container) {
      container.innerHTML = `
        <div class="order-feedback order-feedback-error">
          <div class="order-feedback-content">
            <span class="order-feedback-text">Something went wrong. Please try again.</span>
          </div>
        </div>
      `;
    }
  } finally {
    setButtonLoading(checkoutBtn, false, originalText);
    updateCartUI();
  }
}

async function handleCheckout() {
  return handleCheckoutFlow();
  const cart = getCart();
  if (cart.length === 0) {
    alert("Your cart is empty!");
    return;
  }

  // Show loading message
  const checkoutBtn = document.getElementById("checkout-btn");
  const originalText = checkoutBtn.textContent;
  checkoutBtn.textContent = "Submitting orders...";
  checkoutBtn.disabled = true;

  try {
    // Submit each cart item as an order
    const submittedOrders = [];
    for (const item of cart) {
      if (item.service && item.fields) {
        const payload = {
          service: item.service,
          fields: item.fields,
        };

        const response = await fetchJson(api.orders, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        submittedOrders.push(response);
      }
    }

    // Don't clear cart - show reorder message instead
    // clearCart(); // Commented out

    // Show success message in cart
    const container = document.getElementById("cart-items-container");
    if (container) {
      container.innerHTML = `
        <div class="order-success-message">
          <div class="success-icon">✅</div>
          <h3>Order Placed Successfully!</h3>
          <p>Your order has been submitted and WhatsApp will open shortly.</p>
          <button class="btn-secondary reorder-btn" id="reorder-btn">Reorder Now</button>
        </div>
      `;
    }

    // Update checkout button to "Reorder Now"
    checkoutBtn.textContent = "Reorder Now";
    checkoutBtn.disabled = false;

    // Add reorder functionality
    checkoutBtn.addEventListener("click", function reorderHandler() {
      // Clear cart and reset modal
      clearCart();
      renderCartModal();
      checkoutBtn.textContent = "Place Order";
      checkoutBtn.disabled = true;
      checkoutBtn.removeEventListener("click", reorderHandler);
      // Re-add the original checkout handler
      checkoutBtn.addEventListener("click", handleCheckout);
    });

    // Open WhatsApp for the submitted orders
    if (submittedOrders.length > 0) {
      // Use the first order's response to open WhatsApp
      setTimeout(() => {
        openWhatsAppOrder(submittedOrders[0]);
      }, 1000); // Small delay to show success message first
    }

  } catch (error) {
    console.error("Error submitting orders:", error);
    alert("Error submitting orders. Please try again.");
    checkoutBtn.textContent = originalText;
    checkoutBtn.disabled = false;
  }
}

function showNotification(message) {
  const notification = document.createElement("div");
  notification.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--primary);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 999;
    animation: slideUp 0.3s ease;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideDown 0.3s ease";
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 2000);
}
