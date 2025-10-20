document.addEventListener("DOMContentLoaded", function () {
  const select = document.querySelector('select[name="image_deposit_choice"]');
  if (!select) return;

  const container = document.createElement("div");
  container.classList.add("field-image_deposit_choice");

  [...select.options].forEach((opt) => {
    if (!opt.value) return; // пропускаем "---"
    const img = document.createElement("img");
    img.src = opt.value;
    img.title = opt.text;
    img.addEventListener("click", () => {
      [...container.querySelectorAll("img")].forEach((i) =>
        i.classList.remove("selected")
      );
      img.classList.add("selected");
      select.value = opt.value;
    });
    container.appendChild(img);
  });

  select.insertAdjacentElement("afterend", container);
});
