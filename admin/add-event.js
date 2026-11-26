
const form = document.getElementById("addEventForm");


const categorySelect = document.getElementById("eventCategory");
const otherCategory = document.getElementById("otherCategory");

function updateCategoryField() {
    const isOther = categorySelect.value === "Other";

    otherCategory.hidden = !isOther;
    otherCategory.style.display = isOther ? "block" : "none";
    otherCategory.required = isOther;

    if (!isOther) {
        otherCategory.value = "";
    }
}

categorySelect.addEventListener("change", updateCategoryField);
updateCategoryField();

const message = document.getElementById("formMessage");




form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const image = document.getElementById("eventImage").files[0];
    const maxSize = 10 * 1024 * 1024;

    if (image && image.size > maxSize) {
        message.textContent = "Image must be 10 MB or smaller.";
        message.className = "error";
        return;
    }

    if (image && !["image/jpeg", "image/png", "image/webp"].includes(image.type)) {
        message.textContent = "Only JPG, PNG and WEBP images are allowed.";
        message.className = "error";
        return;
    }

    const eventData = {
        title: document.getElementById("eventName").value.trim(),
        
category: categorySelect.value === "Other"
    ? otherCategory.value.trim()
    : categorySelect.value,

        event_date: document.getElementById("eventDate").value,
        event_time: document.getElementById("eventTime").value,
        location: document.getElementById("eventLocation").value.trim(),
        description: document.getElementById("eventDescription").value.trim(),
        max_participants: Number(
            document.getElementById("maxParticipants").value
        )
    };

    const button = form.querySelector('button[type="submit"]');
    let savedEventId = null;

    try {
        button.disabled = true;
        message.textContent = "Publishing event...";
        message.className = "";

        // Step 1: Save event in MySQL
        
eventData.ticket_price =
    document.getElementById("ticketType").value === "paid"
        ? Number(document.getElementById("ticketPrice").value)
        : 0;

        const response = await fetch("/api/events", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(eventData)
        });

        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "Event saving failed.");
        }

        savedEventId = result.event_id;

        // Step 2: Upload image if selected
        if (image) {
            message.textContent = "Uploading event image...";

            const formData = new FormData();
            formData.append("image", image);

            const uploadResponse = await fetch(
                `/api/events/${savedEventId}/image`,
                {
                    method: "POST",
                    body: formData
                }
            );

            if (uploadResponse.redirected) {
                window.location.href = uploadResponse.url;
                return;
            }

            const uploadResult = await uploadResponse.json();

            if (!uploadResponse.ok || !uploadResult.success) {
                throw new Error(
                    uploadResult.message || "Image upload failed."
                );
            }
        }

        message.textContent = image
            ? "Event and image uploaded successfully!"
            : "Event published successfully!";

        message.className = "success";
        form.reset();

    } catch (error) {
        console.error(error);

        message.textContent = savedEventId
            ? `Event #${savedEventId} was saved, but image upload failed: ${error.message}. Do not publish again.`
            : error.message || "Server connection error.";

        message.className = "error";

    } finally {
        button.disabled = false;
    }
});

// ==================================
// FREE / PAID EVENT FORM
// ==================================

const ticketTypeInput =
    document.getElementById("ticketType");

const ticketPriceInput =
    document.getElementById("ticketPrice");

const ticketPriceGroup =
    document.getElementById("ticketPriceGroup");

function updateTicketType() {
    const isPaid = ticketTypeInput.value === "paid";

    ticketPriceGroup.style.display =
        isPaid ? "block" : "none";

    ticketPriceInput.required = isPaid;
    ticketPriceInput.disabled = !isPaid;

    if (!isPaid) {
        ticketPriceInput.value = "";
    }
}

ticketTypeInput.addEventListener(
    "change",
    updateTicketType
);

updateTicketType();
