// CoralNet + SAM Phase 3 Interactive Dashboard
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const colabUrlInput = document.getElementById("colab-url-input");
  const btnTestColab = document.getElementById("btn-test-colab");
  const colabStatusBadge = document.getElementById("colab-status-badge");
  const colabStatusText = document.getElementById("colab-status-text");

  const imageSelect = document.getElementById("image-select");
  const thumbnailStrip = document.getElementById("thumbnail-strip");
  const fileInput = document.getElementById("file-input");

  const minAreaSlider = document.getElementById("min-area-slider");
  const minAreaInput = document.getElementById("min-area-input");
  const minAreaVal = document.getElementById("min-area-val");
  const iouSlider = document.getElementById("iou-slider");
  const iouVal = document.getElementById("iou-val");

  const quadratW = document.getElementById("quadrat-w");
  const quadratH = document.getElementById("quadrat-h");
  const quadratAreaLabel = document.getElementById("quadrat-area-label");

  const btnRun = document.getElementById("btn-run");
  const btnRunText = document.getElementById("btn-run-text");

  const viewerPlaceholder = document.getElementById("viewer-placeholder");
  const viewerLoading = document.getElementById("viewer-loading");
  const loadingTitle = document.getElementById("loading-title");
  const loadingSubtext = document.getElementById("loading-subtext");

  const interactiveStage = document.getElementById("interactive-stage");
  const stageImage = document.getElementById("stage-image");
  const stageSvg = document.getElementById("stage-svg");
  const colonyTooltip = document.getElementById("colony-tooltip");

  const renderedStage = document.getElementById("rendered-stage");
  const renderedImage = document.getElementById("rendered-image");

  const btnModeInteractive = document.getElementById("btn-mode-interactive");
  const btnModeRendered = document.getElementById("btn-mode-rendered");
  const opacityControl = document.getElementById("opacity-control");
  const opacitySlider = document.getElementById("opacity-slider");
  const opacityVal = document.getElementById("opacity-val");
  const btnDownloadCsv = document.getElementById("btn-download-csv");

  const imageNameBadge = document.getElementById("image-name-badge");
  const colonyCountBadge = document.getElementById("colony-count-badge");
  const resultsPanel = document.getElementById("results-panel");
  const resultsMeta = document.getElementById("results-meta");
  const coverageBarsGrid = document.getElementById("coverage-bars-grid");
  const speciesTbody = document.getElementById("species-tbody");

  let currentResult = null;
  let activeViewMode = "interactive"; // 'interactive' or 'rendered'

  // 1. Min Area Slider & Direct Input
  minAreaSlider.addEventListener("input", (e) => {
    if (minAreaInput) minAreaInput.value = e.target.value;
  });

  if (minAreaInput) {
    minAreaInput.addEventListener("input", (e) => {
      let val = parseInt(e.target.value, 10);
      if (!isNaN(val)) {
        if (val > parseInt(minAreaSlider.max, 10)) {
          minAreaSlider.max = val;
        }
        minAreaSlider.value = val;
      }
    });
  }

  iouSlider.addEventListener("input", (e) => {
    iouVal.textContent = parseFloat(e.target.value).toFixed(2);
  });

  function updateQuadratArea() {
    const w = parseFloat(quadratW.value) || 50;
    const h = parseFloat(quadratH.value) || 50;
    quadratAreaLabel.textContent = `${(w * h).toFixed(0)} cm²`;
  }
  quadratW.addEventListener("input", updateQuadratArea);
  quadratH.addEventListener("input", updateQuadratArea);

  // 2. Colab Health Check
  async function testColabConnection() {
    const url = colabUrlInput.value.trim();
    if (!url) {
      colabStatusBadge.className = "badge badge-offline";
      colabStatusText.textContent = "Colab SAM: Nenhuma URL";
      return;
    }

    colabStatusText.textContent = "Verificando...";
    btnTestColab.disabled = true;

    try {
      const resp = await fetch("/api/test-colab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ colab_url: url })
      });
      const data = await resp.json();

      if (data.connected) {
        colabStatusBadge.className = "badge badge-online";
        colabStatusText.textContent = `🟢 SAM ViT-H Online (${data.gpu_name || "Tesla T4"})`;
      } else {
        colabStatusBadge.className = "badge badge-offline";
        colabStatusText.textContent = "🔴 Servidor Inacessível";
      }
    } catch (err) {
      colabStatusBadge.className = "badge badge-offline";
      colabStatusText.textContent = "🔴 Erro de Conexão";
    } finally {
      btnTestColab.disabled = false;
    }
  }

  btnTestColab.addEventListener("click", testColabConnection);
  // Auto-test on load if default URL exists
  if (colabUrlInput.value) {
    setTimeout(testColabConnection, 500);
  }

  // 3. Load Images
  async function loadImages() {
    try {
      const resp = await fetch("/api/images");
      const data = await resp.json();

      imageSelect.innerHTML = "";
      thumbnailStrip.innerHTML = "";

      if (!data.images || data.images.length === 0) {
        imageSelect.innerHTML = "<option value=''>Nenhuma foto encontrada</option>";
        return;
      }

      data.images.forEach((img, idx) => {
        // Select option
        const opt = document.createElement("option");
        opt.value = img.filename;
        opt.textContent = `${img.filename} (${img.size_mb} MB)`;
        if (idx === 0) opt.selected = true;
        imageSelect.appendChild(opt);

        // Thumbnail item
        const thumb = document.createElement("div");
        thumb.className = `thumb-item ${idx === 0 ? "active" : ""}`;
        thumb.title = img.filename;
        thumb.innerHTML = `<img src="${img.url}" alt="${img.filename}">`;
        thumb.addEventListener("click", () => {
          imageSelect.value = img.filename;
          updateActiveThumb(img.filename);
        });
        thumbnailStrip.appendChild(thumb);
      });
    } catch (err) {
      console.error("Erro ao listar fotos:", err);
    }
  }

  function updateActiveThumb(filename) {
    document.querySelectorAll(".thumb-item").forEach((el) => {
      el.classList.toggle("active", el.title === filename);
    });
  }

  imageSelect.addEventListener("change", (e) => {
    updateActiveThumb(e.target.value);
  });

  // Upload image
  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await resp.json();
      if (data.success) {
        await loadImages();
        imageSelect.value = data.filename;
        updateActiveThumb(data.filename);
      } else {
        alert(data.error || "Erro ao enviar imagem.");
      }
    } catch (err) {
      alert("Falha no upload da foto.");
    }
  });

  // 4. View Mode Toggles & Opacity
  btnModeInteractive.addEventListener("click", () => {
    activeViewMode = "interactive";
    btnModeInteractive.classList.add("active");
    btnModeRendered.classList.remove("active");
    interactiveStage.style.display = "flex";
    renderedStage.style.display = "none";
    opacityControl.style.display = "flex";
  });

  btnModeRendered.addEventListener("click", () => {
    activeViewMode = "rendered";
    btnModeRendered.classList.add("active");
    btnModeInteractive.classList.remove("active");
    interactiveStage.style.display = "none";
    renderedStage.style.display = "flex";
    opacityControl.style.display = "none";
  });

  opacitySlider.addEventListener("input", (e) => {
    const val = e.target.value;
    opacityVal.textContent = `${val}%`;
    const alpha = val / 100.0;
    document.querySelectorAll(".colony-polygon").forEach((poly) => {
      poly.style.fillOpacity = alpha;
    });
  });

  // 5. Run Pipeline
  btnRun.addEventListener("click", async () => {
    const imageName = imageSelect.value;
    if (!imageName) {
      alert("Selecione uma imagem de transecto.");
      return;
    }

    const minArea = minAreaInput
      ? parseInt(minAreaInput.value, 10) || parseInt(minAreaSlider.value, 10)
      : parseInt(minAreaSlider.value, 10);
    const iouThresh = parseFloat(iouSlider.value);
    const quadratWVal = parseFloat(quadratW.value) || 50;
    const quadratHVal = parseFloat(quadratH.value) || 50;

    btnRun.disabled = true;
    btnRunText.textContent = "Processando...";
    viewerPlaceholder.style.display = "none";
    interactiveStage.style.display = "none";
    renderedStage.style.display = "none";
    resultsPanel.style.display = "none";
    viewerLoading.style.display = "flex";

    loadingTitle.textContent = "Segmentando Transecto Bêntico...";
    loadingSubtext.textContent = colabUrl
      ? "SAM ViT-H delimitando colônias na GPU Tesla T4..."
      : "Processando em modo simulado local...";

    try {
      const resp = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_name: imageName,
          colab_url: colabUrl,
          min_area: minArea,
          iou_thresh: iouThresh,
          n_points: 5,
          quadrat_width_cm: quadratWVal,
          quadrat_height_cm: quadratHVal
        })
      });

      const json = await resp.json();
      if (!json.success) {
        throw new Error(json.error || "Erro durante o processamento do pipeline.");
      }

      currentResult = json.data;
      renderResults(currentResult);
    } catch (err) {
      alert(`Erro: ${err.message}`);
      viewerPlaceholder.style.display = "flex";
    } finally {
      viewerLoading.style.display = "none";
      btnRun.disabled = false;
      btnRunText.textContent = "Executar SAM ➔ CoralNet";
    }
  });

  // 6. Render Results
  function renderResults(res) {
    // Toolbar update
    imageNameBadge.textContent = `${res.image_filename} (${res.image_width}x${res.image_height} px)`;
    colonyCountBadge.style.display = "inline-flex";
    colonyCountBadge.textContent = `${res.total_colonies} colônias identificadas`;

    // Static Image
    renderedImage.src = `/output/${res.output_image_filename}?t=${Date.now()}`;

    // Interactive Image
    stageImage.src = `/images/${res.image_filename}`;
    stageSvg.setAttribute("viewBox", `0 0 ${res.image_width} ${res.image_height}`);
    stageSvg.innerHTML = "";

    const alpha = opacitySlider.value / 100.0;

    // Draw Polygons in SVG
    res.colonies.forEach((col) => {
      const polyPts = col.polygon;
      if (!polyPts || polyPts.length < 3) return;

      const ptsStr = polyPts.map((p) => `${p[0]},${p[1]}`).join(" ");

      const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
      polygon.setAttribute("points", ptsStr);
      polygon.setAttribute("fill", col.color);
      polygon.setAttribute("fill-opacity", alpha);
      polygon.setAttribute("stroke", col.color);
      polygon.setAttribute("stroke-width", "1.6");
      polygon.setAttribute("class", "colony-polygon");
      polygon.setAttribute("data-id", col.id);
      polygon.setAttribute("data-genus", col.genus);

      // Mouse events
      polygon.addEventListener("mouseenter", (e) => {
        showTooltip(e, col);
      });
      polygon.addEventListener("mousemove", (e) => {
        moveTooltip(e);
      });
      polygon.addEventListener("mouseleave", () => {
        hideTooltip();
      });

      stageSvg.appendChild(polygon);

      // Multi-point crosshairs
      if (col.sample_points && col.sample_points.length > 1) {
        col.sample_points.forEach(([r, c]) => {
          const crossSize = 5;
          const lineH = document.createElementNS("http://www.w3.org/2000/svg", "line");
          lineH.setAttribute("x1", c - crossSize);
          lineH.setAttribute("y1", r);
          lineH.setAttribute("x2", c + crossSize);
          lineH.setAttribute("y2", r);
          lineH.setAttribute("class", "sample-cross");

          const lineV = document.createElementNS("http://www.w3.org/2000/svg", "line");
          lineV.setAttribute("x1", c);
          lineV.setAttribute("y1", r - crossSize);
          lineV.setAttribute("x2", c);
          lineV.setAttribute("y2", r + crossSize);
          lineV.setAttribute("class", "sample-cross");

          stageSvg.appendChild(lineH);
          stageSvg.appendChild(lineV);
        });
      }
    });

    // CSV Download Button
    btnDownloadCsv.style.display = "inline-flex";
    btnDownloadCsv.onclick = () => {
      window.location.href = `/api/download/csv/${res.output_csv_filename}`;
    };

    // Show appropriate stage
    opacityControl.style.display = activeViewMode === "interactive" ? "flex" : "none";
    interactiveStage.style.display = activeViewMode === "interactive" ? "flex" : "none";
    renderedStage.style.display = activeViewMode === "rendered" ? "flex" : "none";

    // Results Panel
    resultsPanel.style.display = "block";
    resultsMeta.textContent = `Quadrante: ${res.quadrat_width_cm}x${res.quadrat_height_cm} cm (${res.total_area_cm2} cm²) | Suprimidas pelo NMS: ${res.suppressed_redundant_masks} duplicatas | Votação Multi-Ponto: ${res.multi_point_colonies} colônias`;

    // Coverage Bars Grid
    coverageBarsGrid.innerHTML = "";
    res.genus_summary.forEach((item) => {
      const card = document.createElement("div");
      card.className = "coverage-bar-card";
      card.innerHTML = `
        <div class="bar-title-row">
          <span class="bar-genus-label">
            <span class="tooltip-color-dot" style="background-color: ${item.color};"></span>
            ${item.genus}
          </span>
          <strong>${item.coverage_pct}%</strong>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${item.coverage_pct}%; background-color: ${item.color};"></div>
        </div>
        <div class="bar-details-row">
          <span>${item.count} colônias</span>
          <span>${item.area_cm2} cm²</span>
        </div>
      `;

      card.addEventListener("mouseenter", () => highlightGenus(item.genus, true));
      card.addEventListener("mouseleave", () => highlightGenus(item.genus, false));

      coverageBarsGrid.appendChild(card);
    });

    // Species Table
    speciesTbody.innerHTML = "";
    res.genus_summary.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="species-color-swatch" style="background-color: ${item.color};"></span></td>
        <td><strong>${item.genus}</strong></td>
        <td>${item.count}</td>
        <td>${item.area_cm2} cm²</td>
        <td><strong>${item.coverage_pct}%</strong></td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="filterByGenus('${item.genus}')">Destacar</button>
        </td>
      `;
      tr.addEventListener("mouseenter", () => highlightGenus(item.genus, true));
      tr.addEventListener("mouseleave", () => highlightGenus(item.genus, false));
      speciesTbody.appendChild(tr);
    });
  }

  // Tooltip functions
  function showTooltip(e, col) {
    colonyTooltip.innerHTML = `
      <div class="tooltip-genus">
        <span class="tooltip-color-dot" style="background-color: ${col.color};"></span>
        #${col.id} ${col.genus}
      </div>
      <div>Área: <strong>${col.area_cm2} cm²</strong> (${col.area_pixels} px &bull; ${col.area_pct}%)</div>
      <div>Confiança: <strong>${(col.confidence * 100).toFixed(1)}%</strong> &bull; Consenso: <strong>${(col.consensus_ratio * 100).toFixed(0)}%</strong></div>
      <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 2px;">Sondagens: ${col.sample_points_count} pontos internos</div>
    `;
    colonyTooltip.style.display = "block";
    moveTooltip(e);
  }

  function moveTooltip(e) {
    const stageRect = interactiveStage.getBoundingClientRect();
    const x = e.clientX - stageRect.left;
    const y = e.clientY - stageRect.top;
    colonyTooltip.style.left = `${x}px`;
    colonyTooltip.style.top = `${y}px`;
  }

  function hideTooltip() {
    colonyTooltip.style.display = "none";
  }

  function highlightGenus(genus, active) {
    document.querySelectorAll(".colony-polygon").forEach((poly) => {
      if (active) {
        if (poly.getAttribute("data-genus") === genus) {
          poly.style.stroke = "#ffffff";
          poly.style.strokeWidth = "3px";
          poly.style.fillOpacity = "0.75";
        } else {
          poly.style.fillOpacity = "0.1";
        }
      } else {
        poly.style.stroke = poly.getAttribute("fill");
        poly.style.strokeWidth = "1.6px";
        poly.style.fillOpacity = opacitySlider.value / 100.0;
      }
    });
  }

  window.filterByGenus = function (genus) {
    highlightGenus(genus, true);
    setTimeout(() => {
      highlightGenus(genus, false);
    }, 2500);
  };

  // Initial load
  loadImages();
});
