const tipsCategory = document.getElementById("tipsCategory");

if (tipsCategory) {
  tipsCategory.addEventListener("change", () => {
    const selected = tipsCategory.value;
    const tips = document.querySelectorAll("#tipsList .card");

    tips.forEach((card) => {
      const category = card.getAttribute("data-category");
      const show = selected === "all" || category === selected;
      card.style.display = show ? "block" : "none";
    });
  });
}
