
// EventHub Home Page

const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");

searchForm.addEventListener("submit", function(event) {
    event.preventDefault();

    const query = searchInput.value.trim();

    if (query === "") {
        document.getElementById("upcoming-events")
            .scrollIntoView({ behavior: "smooth" });
        return;
    }

    // Search will be connected to database later.
    alert("Event search will be available after database integration.");
});

// Future functionality:
// 1. Fetch events from backend
// 2. Display event cards dynamically
// 3. Hide empty state when events exist
// 4. Filter events using search

const logoutBtn = document.getElementById("logoutBtn");

logoutBtn.addEventListener("click", async function() {
    const response = await fetch("/logout", {
        method: "POST"
    });

    if (response.ok) {
        window.location.href = "/login.html";
    } else {
        alert("Logout failed. Please try again.");
    }
});


document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("eventsContainer");
    const emptyState = document.getElementById("emptyState");

    if (!container || !emptyState) return;

    try {
        const response = await fetch("/api/events");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error("Failed to load events");
        }

        container.replaceChildren();

        if (data.events.length === 0) {
            emptyState.style.display = "";
            return;
        }

        emptyState.style.display = "none";

        data.events.forEach(event => {
            const card = document.createElement("a");
            card.className = "event-card";

            card.href = `/event-details.html?id=${event.event_id}`;
            card.setAttribute("aria-label", `View details for ${event.title}`);


            const icon = document.createElement("div");
            icon.className = "event-card-icon";
            
if (event.image_path) {
    const image = document.createElement("img");

    image.src = event.image_path;
    image.alt = event.title;
    image.loading = "lazy";

    image.onerror = function () {
        image.remove();
        icon.textContent = "📅";
    };

    icon.appendChild(image);
} else {
    icon.textContent = "📅";
}


            const category = document.createElement("span");
            category.className = "event-category";
            category.textContent = event.category;

            const title = document.createElement("h3");
            title.textContent = event.title;

            const date = document.createElement("p");
            date.textContent =
                "🗓 " + event.event_date + " | " + event.event_time;

            const location = document.createElement("p");
            location.textContent = "📍 " + event.location;

            const description = document.createElement("p");
            description.className = "event-description";
            description.textContent = event.description || "";

            card.append(
                icon,
                category,
                title,
                date,
                location,
                description
            );

            container.appendChild(card);
        });

    } catch (error) {
        console.error("Event loading error:", error);
        emptyState.style.display = "none";
        container.textContent = "Could not load events.";
    }
});


document.addEventListener("DOMContentLoaded", async () => {
    const header = document.querySelector("header");
    if (!header) return;

    const items = Array.from(
        header.querySelectorAll("a, button")
    );

    const findItems = (label) =>
        items.filter(item =>
            item.textContent.trim().toLowerCase() === label
        );

    const loginLinks = findItems("login");
    const bookingLinks = findItems("my bookings");
    const logoutButtons = findItems("logout");

    function showOnlyFirst(elements, visible) {
        elements.forEach((element, index) => {
            element.style.display =
                visible && index === 0 ? "" : "none";
        });
    }

    try {
        const response = await fetch("/api/auth/status", {
            credentials: "same-origin",
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not check login status");
        }

        const data = await response.json();
        const role = data.logged_in ? data.role : null;

        showOnlyFirst(loginLinks, !role);
        showOnlyFirst(bookingLinks, role === "user");
        showOnlyFirst(logoutButtons, !!role);

        if (role === "admin") {
            const dashboardLink =
                document.createElement("a");

            dashboardLink.href = "/admin/dashboard.html";
            dashboardLink.textContent = "Admin Dashboard";
            dashboardLink.style.marginLeft = "15px";

            const target = loginLinks[0] || bookingLinks[0];

            if (target) {
                target.insertAdjacentElement(
                    "afterend",
                    dashboardLink
                );
            } else {
                header.appendChild(dashboardLink);
            }
        }

    } catch (error) {
        console.error("Navigation error:", error);

        // Safe fallback when login status cannot be checked
        showOnlyFirst(loginLinks, true);
        showOnlyFirst(bookingLinks, false);
        showOnlyFirst(logoutButtons, false);
    }
});
