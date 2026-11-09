/* Load a YouTube video only when the reader asks for it.
   Without JavaScript the poster is a plain link to YouTube. */
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var link = event.target.closest(".video-embed__link");
    if (!link || !link.dataset.video) return;

    event.preventDefault();
    var iframe = document.createElement("iframe");
    iframe.src = "https://www.youtube-nocookie.com/embed/" + link.dataset.video + "?autoplay=1";
    iframe.title = "YouTube";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.allowFullscreen = true;
    iframe.loading = "lazy";
    link.replaceWith(iframe);
  });
})();
