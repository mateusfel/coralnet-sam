// CoralSCOP + CoralNet Interactive Benthic Segmentation Dashboard
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const colabUrlInput = document.getElementById("colab-url-input");
  const btnTestColab = document.getElementById("btn-test-colab");
  const colabStatusBadge = document.getElementById("colab-status-badge");
  const colabStatusText = document.getElementById("colab-status-text");

  const imageSelect = document.getElementById("image-select");
  const thumbnailStrip = document.getElementById("thumbnail-strip");
  const fileInput = document.getElementById("file-input");

  // Filter & Quadrat ROI Controls
  const filterModeSelect = document.getElementById("filter-mode-select");
  const btnPreviewFilter = document.getElementById("btn-preview-filter");
  const btnStartQuadrat = document.getElementById("btn-start-quadrat");
  const btnClearQuadrat = document.getElementById("btn-clear-quadrat");
  const quadratRoiBadge = document.getElementById("quadrat-roi-badge");
  const quadratBanner = document.getElementById("quadrat-banner");
  const quadratBannerText = document.getElementById("quadrat-banner-text");
  const btnCancelQuadrat = document.getElementById("btn-cancel-quadrat");
  const btnToggleBg = document.getElementById("btn-toggle-bg");

  const minAreaSlider = document.getElementById("min-area-slider");
  const minAreaInput = document.getElementById("min-area-input");
  const iouSlider = document.getElementById("iou-slider");
  const iouVal = document.getElementById("iou-val");

  const quadratW = document.getElementById("quadrat-w");
  const quadratH = document.getElementById("quadrat-h");
  const quadratAreaLabel = document.getElementById("quadrat-area-label");

  // CoralSCOP Hyperparameter Controls
  const toggleSamParams = document.getElementById("toggle-sam-params");
  const samAccordionArrow = document.getElementById("sam-accordion-arrow");
  const samParamsContent = document.getElementById("sam-params-content");

  const samPointsPerSide = document.getElementById("sam-points-per-side");
  const samPointsVal = document.getElementById("sam-points-val");
  const samPointsTotal = document.getElementById("sam-points-total");
  const samPredIouSlider = document.getElementById("sam-pred-iou-slider");
  const samPredIouVal = document.getElementById("sam-pred-iou-val");
  const samStabilitySlider = document.getElementById("sam-stability-slider");
  const samStabilityVal = document.getElementById("sam-stability-val");
  const samCropLayers = document.getElementById("sam-crop-layers");
  const samCropLayersVal = document.getElementById("sam-crop-layers-val");
  const samCropDownscale = document.getElementById("sam-crop-downscale");
  const samCropDownscaleVal = document.getElementById("sam-crop-downscale-val");
  const btnResetSamParams = document.getElementById("btn-reset-sam-params");

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

  // Application State
  let currentResult = null;
  let activeViewMode = "interactive"; // 'interactive' or 'rendered'
  let currentImageDimensions = { width: 4000, height: 3000 };
  const quadratCornersByImage = {}; // { [filename]: [[x,y],[x,y],[x,y],[x,y]] }
  const enhancedUrlByImage = {}; // { [filename]: "/output/..." }
  let showingEnhancedBg = false;

  // Quadrat Picking / Dragging State
  let isPickingQuadrat = false;
  let pickingCorners = [];
  let draggingCornerIdx = null;

  // Restore saved Colab URL from localStorage
  const savedColabUrl = localStorage.getItem("coralscop_colab_url");
  if (savedColabUrl && colabUrlInput) {
    colabUrlInput.value = savedColabUrl;
  }
  if (colabUrlInput) {
    colabUrlInput.addEventListener("change", () => {
      localStorage.setItem("coralscop_colab_url", colabUrlInput.value.trim());
    });
  }

  // Canonical ordering [TL, TR, BR, BL] matching src/preprocessing.py
  function orderQuadCornersJs(pts) {
    if (!pts || pts.length !== 4) return pts;
    const copy = pts.map((p) => [p[0], p[1]]);
    copy.sort((a, b) => a[1] - b[1]);
    const topPair = copy.slice(0, 2).sort((a, b) => a[0] - b[0]);
    const botPair = copy.slice(2, 4).sort((a, b) => a[0] - b[0]);
    return [topPair[0], topPair[1], botPair[1], botPair[0]];
  }

  // Convert screen mouse event to SVG viewBox pixel coordinates
  function clientToSvgCoords(evt) {
    const ctm = stageSvg.getScreenCTM();
    if (ctm) {
      const pt = stageSvg.createSVGPoint();
      pt.x = evt.clientX;
      pt.y = evt.clientY;
      const svgPt = pt.matrixTransform(ctm.inverse());
      return [
        Math.max(0, Math.min(currentImageDimensions.width, Math.round(svgPt.x))),
        Math.max(0, Math.min(currentImageDimensions.height, Math.round(svgPt.y)))
      ];
    }
    const rect = stageImage.getBoundingClientRect();
    const rx = (evt.clientX - rect.left) / Math.max(1, rect.width);
    const ry = (evt.clientY - rect.top) / Math.max(1, rect.height);
    return [
      Math.max(0, Math.min(currentImageDimensions.width, Math.round(rx * currentImageDimensions.width))),
      Math.max(0, Math.min(currentImageDimensions.height, Math.round(ry * currentImageDimensions.height)))
    ];
  }

  // 1. Sliders & Scale Inputs
  minAreaSlider.addEventListener("input", (e) => {
    if (minAreaInput) minAreaInput.value = e.target.value;
  });

  if (minAreaInput) {
    minAreaInput.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
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

  // Accordion Toggle
  if (toggleSamParams && samParamsContent) {
    toggleSamParams.addEventListener("click", () => {
      const isHidden = samParamsContent.style.display === "none";
      samParamsContent.style.display = isHidden ? "block" : "none";
      if (samAccordionArrow) {
        samAccordionArrow.classList.toggle("open", isHidden);
      }
    });
  }

  // CoralSCOP Hyperparameter Inputs
  if (samPointsPerSide) {
    samPointsPerSide.addEventListener("change", (e) => {
      const val = parseInt(e.target.value, 10);
      if (samPointsVal) samPointsVal.textContent = val;
      if (samPointsTotal) samPointsTotal.textContent = (val * val).toLocaleString("pt-BR");
    });
  }

  if (samPredIouSlider) {
    samPredIouSlider.addEventListener("input", (e) => {
      if (samPredIouVal) samPredIouVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (samStabilitySlider) {
    samStabilitySlider.addEventListener("input", (e) => {
      if (samStabilityVal) samStabilityVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (samCropLayers) {
    samCropLayers.addEventListener("change", (e) => {
      if (samCropLayersVal) samCropLayersVal.textContent = e.target.value;
    });
  }

  if (samCropDownscale) {
    samCropDownscale.addEventListener("change", (e) => {
      if (samCropDownscaleVal) samCropDownscaleVal.textContent = e.target.value;
    });
  }

  // Reset to Official CoralSCOP Defaults (CVPR 2024: pts=32, pred_iou=0.72, stability=0.62)
  if (btnResetSamParams) {
    btnResetSamParams.addEventListener("click", () => {
      if (samPointsPerSide) {
        samPointsPerSide.value = "32";
        if (samPointsVal) samPointsVal.textContent = "32";
        if (samPointsTotal) samPointsTotal.textContent = "1.024";
      }
      if (samPredIouSlider) {
        samPredIouSlider.value = "0.72";
        if (samPredIouVal) samPredIouVal.textContent = "0.72";
      }
      if (samStabilitySlider) {
        samStabilitySlider.value = "0.62";
        if (samStabilityVal) samStabilityVal.textContent = "0.62";
      }
      if (samCropLayers) {
        samCropLayers.value = "1";
        if (samCropLayersVal) samCropLayersVal.textContent = "1";
      }
      if (samCropDownscale) {
        samCropDownscale.value = "2";
        if (samCropDownscaleVal) samCropDownscaleVal.textContent = "2";
      }
    });
  }

  // 2. Colab Health Check
  async function testColabConnection() {
    const url = colabUrlInput.value.trim();
    if (!url) {
      colabStatusBadge.className = "badge badge-offline";
      colabStatusText.textContent = "Colab GPU: Nenhuma URL";
      return;
    }

    localStorage.setItem("coralscop_colab_url", url);
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
        if (data.is_coralscop) {
          colabStatusBadge.className = "badge badge-online";
          colabStatusText.textContent = `🟢 CoralSCOP Online (${data.gpu_name || "Tesla T4"})`;
        } else {
          colabStatusBadge.className = "badge badge-warning";
          colabStatusText.textContent = `🟡 ${data.model || "SAM Antigo"} (Atualize o Colab p/ CoralSCOP)`;
        }
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
  if (colabUrlInput.value) {
    setTimeout(testColabConnection, 400);
  }

  // 3. Immediate Photo Preview & Quadrat ROI Overlay Rendering
  function updateQuadratUiState() {
    const imgName = imageSelect.value;
    const savedCorners = imgName ? quadratCornersByImage[imgName] : null;

    if (isPickingQuadrat) {
      quadratRoiBadge.className = "roi-status-pill roi-picking";
      quadratRoiBadge.textContent = `Marcando (${pickingCorners.length}/4)`;
      if (quadratBanner) {
        quadratBanner.style.display = "flex";
        quadratBannerText.textContent = `📐 Clique no canto interno ${pickingCorners.length + 1} de 4 do quadrante de PVC...`;
      }
      stageSvg.classList.add("picking-quadrat");
      btnStartQuadrat.textContent = `⏳ Marcando (${pickingCorners.length}/4)...`;
      btnClearQuadrat.style.display = "none";
    } else {
      if (quadratBanner) quadratBanner.style.display = "none";
      stageSvg.classList.remove("picking-quadrat");

      if (savedCorners && savedCorners.length === 4) {
        quadratRoiBadge.className = "roi-status-pill roi-active";
        quadratRoiBadge.textContent = "✅ 4 Cantos (Homografia)";
        btnStartQuadrat.textContent = "📐 Remarcar 4 Cantos";
        btnClearQuadrat.style.display = "inline-flex";
      } else {
        quadratRoiBadge.className = "roi-status-pill roi-inactive";
        quadratRoiBadge.textContent = "Foto Inteira";
        btnStartQuadrat.textContent = "📐 Marcar 4 Cantos";
        btnClearQuadrat.style.display = "none";
      }
    }
  }

  function updateBgToggleUi() {
    const imgName = imageSelect.value;
    const hasEnhanced = Boolean(imgName && enhancedUrlByImage[imgName]);
    if (!btnToggleBg) return;

    if (hasEnhanced) {
      btnToggleBg.style.display = "inline-flex";
      btnToggleBg.textContent = showingEnhancedBg ? "✨ Fundo: Realçado" : "🖼️ Fundo: Original";
    } else {
      btnToggleBg.style.display = "none";
    }
  }

  function redrawSvgScene() {
    stageSvg.innerHTML = "";
    const imgName = imageSelect.value;
    const alpha = opacitySlider.value / 100.0;

    // 1. Draw Colony Polygons if currentResult matches selected image
    if (currentResult && currentResult.image_filename === imgName) {
      currentResult.colonies.forEach((col) => {
        const polyList =
          col.polygons && col.polygons.length > 0
            ? col.polygons
            : col.polygon && col.polygon.length >= 3
            ? [col.polygon]
            : [];

        polyList.forEach((polyPts) => {
          if (!polyPts || polyPts.length < 3) return;
          const ptsStr = polyPts.map((p) => `${p[0]},${p[1]}`).join(" ");

          const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
          polygon.setAttribute("points", ptsStr);
          polygon.setAttribute("fill", col.color);
          polygon.setAttribute("fill-opacity", alpha);
          polygon.setAttribute("stroke", col.color);
          polygon.setAttribute("stroke-width", "3.5");
          polygon.setAttribute("class", "colony-polygon");
          polygon.setAttribute("data-id", col.id);
          polygon.setAttribute("data-genus", col.genus);

          polygon.addEventListener("mouseenter", (e) => {
            if (!isPickingQuadrat) showTooltip(e, col);
          });
          polygon.addEventListener("mousemove", (e) => {
            if (!isPickingQuadrat) moveTooltip(e);
          });
          polygon.addEventListener("mouseleave", () => {
            hideTooltip();
          });

          stageSvg.appendChild(polygon);
        });

        // Multi-point interior crosshairs
        if (col.sample_points && col.sample_points.length > 1) {
          col.sample_points.forEach(([r, c]) => {
            const crossSize = Math.max(6, Math.round(currentImageDimensions.width * 0.002));
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
    }

    // 2. Draw 4-Corner Quadrat Overlay (either in-progress pickingCorners or saved corners)
    const activePts = isPickingQuadrat
      ? pickingCorners
      : imgName && quadratCornersByImage[imgName]
      ? quadratCornersByImage[imgName]
      : [];

    if (activePts && activePts.length > 0) {
      const handleRadius = Math.max(16, Math.round(currentImageDimensions.width * 0.0075));
      const fontSize = Math.max(16, Math.round(handleRadius * 1.15));

      if (activePts.length === 4) {
        const polyEl = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        polyEl.setAttribute("points", activePts.map((p) => `${p[0]},${p[1]}`).join(" "));
        polyEl.setAttribute("class", "quadrat-roi-polygon");
        stageSvg.appendChild(polyEl);
      } else if (activePts.length >= 2) {
        const lineEl = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        lineEl.setAttribute("points", activePts.map((p) => `${p[0]},${p[1]}`).join(" "));
        lineEl.setAttribute("class", "quadrat-roi-polyline");
        stageSvg.appendChild(lineEl);
      }

      activePts.forEach((pt, idx) => {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", pt[0]);
        circle.setAttribute("cy", pt[1]);
        circle.setAttribute("r", handleRadius);
        circle.setAttribute("fill", activePts.length === 4 ? "#38bdf8" : "#fbbf24");
        circle.setAttribute("stroke", "#0f172a");
        circle.setAttribute("stroke-width", Math.max(3, Math.round(handleRadius * 0.2)));
        circle.setAttribute("class", "quadrat-corner-handle");

        if (!isPickingQuadrat && activePts.length === 4) {
          circle.addEventListener("mousedown", (e) => {
            e.stopPropagation();
            draggingCornerIdx = idx;
          });
        }

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", pt[0]);
        label.setAttribute("y", pt[1]);
        label.setAttribute("font-size", `${fontSize}px`);
        label.setAttribute("class", "quadrat-corner-label");
        label.textContent = String(idx + 1);

        stageSvg.appendChild(circle);
        stageSvg.appendChild(label);
      });
    }
  }

  function showImageInStage(filename) {
    if (!filename) return;
    isPickingQuadrat = false;
    pickingCorners = [];
    draggingCornerIdx = null;

    if (!currentResult || currentResult.image_filename !== filename) {
      colonyCountBadge.style.display = "none";
      resultsPanel.style.display = "none";
      btnDownloadCsv.style.display = "none";
      opacityControl.style.display = "none";
      activeViewMode = "interactive";
      btnModeInteractive.classList.add("active");
      btnModeRendered.classList.remove("active");
    }

    showingEnhancedBg = Boolean(enhancedUrlByImage[filename] && showingEnhancedBg);
    const targetSrc =
      showingEnhancedBg && enhancedUrlByImage[filename]
        ? enhancedUrlByImage[filename]
        : `/images/${filename}`;

    viewerPlaceholder.style.display = "none";
    renderedStage.style.display = activeViewMode === "rendered" ? "flex" : "none";
    interactiveStage.style.display = activeViewMode === "interactive" ? "flex" : "none";

    stageImage.onload = () => {
      const nw = stageImage.naturalWidth || 4000;
      const nh = stageImage.naturalHeight || 3000;
      currentImageDimensions = { width: nw, height: nh };
      stageSvg.setAttribute("viewBox", `0 0 ${nw} ${nh}`);
      imageNameBadge.textContent = `${filename} (${nw}x${nh} px)`;
      updateQuadratUiState();
      updateBgToggleUi();
      redrawSvgScene();
    };
    stageImage.src = targetSrc;
  }

  // SVG Mouse Handlers for 4-Corner Picking & Fine-Tuning Drag
  stageSvg.addEventListener("click", (e) => {
    if (!isPickingQuadrat) return;
    const imgName = imageSelect.value;
    if (!imgName) return;

    const pt = clientToSvgCoords(e);
    pickingCorners.push(pt);

    if (pickingCorners.length === 4) {
      quadratCornersByImage[imgName] = orderQuadCornersJs(pickingCorners);
      isPickingQuadrat = false;
      pickingCorners = [];
    }
    updateQuadratUiState();
    redrawSvgScene();
  });

  window.addEventListener("mousemove", (e) => {
    if (draggingCornerIdx === null) return;
    const imgName = imageSelect.value;
    if (!imgName || !quadratCornersByImage[imgName]) return;
    const pt = clientToSvgCoords(e);
    quadratCornersByImage[imgName][draggingCornerIdx] = pt;
    redrawSvgScene();
  });

  window.addEventListener("mouseup", () => {
    if (draggingCornerIdx !== null) {
      const imgName = imageSelect.value;
      if (imgName && quadratCornersByImage[imgName]) {
        quadratCornersByImage[imgName] = orderQuadCornersJs(quadratCornersByImage[imgName]);
      }
      draggingCornerIdx = null;
      redrawSvgScene();
    }
  });

  if (btnStartQuadrat) {
    btnStartQuadrat.addEventListener("click", () => {
      const imgName = imageSelect.value;
      if (!imgName) {
        alert("Selecione uma foto de transecto primeiro.");
        return;
      }
      if (activeViewMode !== "interactive") {
        btnModeInteractive.click();
      }
      isPickingQuadrat = true;
      pickingCorners = [];
      hideTooltip();
      updateQuadratUiState();
      redrawSvgScene();
    });
  }

  if (btnCancelQuadrat) {
    btnCancelQuadrat.addEventListener("click", (e) => {
      e.stopPropagation();
      isPickingQuadrat = false;
      pickingCorners = [];
      updateQuadratUiState();
      redrawSvgScene();
    });
  }

  if (btnClearQuadrat) {
    btnClearQuadrat.addEventListener("click", () => {
      const imgName = imageSelect.value;
      if (imgName) {
        delete quadratCornersByImage[imgName];
      }
      isPickingQuadrat = false;
      pickingCorners = [];
      updateQuadratUiState();
      redrawSvgScene();
    });
  }

  // Live Underwater Filter Preview Button (runs locally in ~0.3s)
  if (btnPreviewFilter) {
    btnPreviewFilter.addEventListener("click", async () => {
      const imgName = imageSelect.value;
      if (!imgName) return;
      const mode = filterModeSelect ? filterModeSelect.value : "combined";
      if (mode === "none") {
        showingEnhancedBg = false;
        stageImage.src = `/images/${imgName}`;
        updateBgToggleUi();
        return;
      }

      const origText = btnPreviewFilter.textContent;
      btnPreviewFilter.disabled = true;
      btnPreviewFilter.textContent = "⏳ Aplicando realce subaquático...";
      try {
        const resp = await fetch("/api/preview-filter", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: imgName,
            filter_mode: mode,
            quadrat_corners: quadratCornersByImage[imgName] || null
          })
        });
        const data = await resp.json();
        if (data.success && data.preview_url) {
          enhancedUrlByImage[imgName] = data.preview_url;
          showingEnhancedBg = true;
          if (activeViewMode !== "interactive") btnModeInteractive.click();
          stageImage.src = data.preview_url;
          updateBgToggleUi();
        } else {
          alert(data.error || "Erro ao gerar prévia do filtro.");
        }
      } catch (err) {
        alert(`Falha ao gerar prévia do filtro: ${err.message}`);
      } finally {
        btnPreviewFilter.disabled = false;
        btnPreviewFilter.textContent = origText;
      }
    });
  }

  if (btnToggleBg) {
    btnToggleBg.addEventListener("click", () => {
      const imgName = imageSelect.value;
      if (!imgName || !enhancedUrlByImage[imgName]) return;
      showingEnhancedBg = !showingEnhancedBg;
      stageImage.src = showingEnhancedBg ? enhancedUrlByImage[imgName] : `/images/${imgName}`;
      updateBgToggleUi();
    });
  }

  // 4. Load Images
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
        const opt = document.createElement("option");
        opt.value = img.filename;
        opt.textContent = `${img.filename} (${img.size_mb} MB)`;
        if (idx === 0) opt.selected = true;
        imageSelect.appendChild(opt);

        const thumb = document.createElement("div");
        thumb.className = `thumb-item ${idx === 0 ? "active" : ""}`;
        thumb.title = img.filename;
        thumb.innerHTML = `<img src="${img.url}" alt="${img.filename}">`;
        thumb.addEventListener("click", () => {
          imageSelect.value = img.filename;
          updateActiveThumb(img.filename);
          showingEnhancedBg = false;
          showImageInStage(img.filename);
        });
        thumbnailStrip.appendChild(thumb);
      });

      // Immediately show first image so user can inspect or mark 4 corners right away
      showImageInStage(data.images[0].filename);
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
    showingEnhancedBg = false;
    showImageInStage(e.target.value);
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
        showingEnhancedBg = false;
        showImageInStage(data.filename);
      } else {
        alert(data.error || "Erro ao enviar imagem.");
      }
    } catch (err) {
      alert("Falha no upload da foto.");
    }
  });

  // 5. View Mode Toggles & Opacity
  btnModeInteractive.addEventListener("click", () => {
    activeViewMode = "interactive";
    btnModeInteractive.classList.add("active");
    btnModeRendered.classList.remove("active");
    interactiveStage.style.display = "flex";
    renderedStage.style.display = "none";
    if (currentResult) opacityControl.style.display = "flex";
  });

  btnModeRendered.addEventListener("click", () => {
    if (!currentResult) return;
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

  // 6. Run Pipeline
  btnRun.addEventListener("click", async () => {
    const imageName = imageSelect.value;
    if (!imageName) {
      alert("Selecione uma imagem de transecto.");
      return;
    }

    isPickingQuadrat = false;
    pickingCorners = [];

    const colabUrl = colabUrlInput ? colabUrlInput.value.trim() : "";
    if (colabUrl) localStorage.setItem("coralscop_colab_url", colabUrl);

    const minArea = minAreaInput
      ? parseInt(minAreaInput.value, 10) || parseInt(minAreaSlider.value, 10)
      : parseInt(minAreaSlider.value, 10);
    const iouThresh = parseFloat(iouSlider.value);
    const quadratWVal = parseFloat(quadratW.value) || 50;
    const quadratHVal = parseFloat(quadratH.value) || 50;
    const filterMode = filterModeSelect ? filterModeSelect.value : "combined";
    const quadratCorners = quadratCornersByImage[imageName] || null;

    // CoralSCOP Hyperparameters
    const pointsPerSide = samPointsPerSide ? parseInt(samPointsPerSide.value, 10) : 32;
    const predIou = samPredIouSlider ? parseFloat(samPredIouSlider.value) : 0.72;
    const stabilityScore = samStabilitySlider ? parseFloat(samStabilitySlider.value) : 0.62;
    const cropLayers = samCropLayers ? parseInt(samCropLayers.value, 10) : 1;
    const cropDownscale = samCropDownscale ? parseInt(samCropDownscale.value, 10) : 2;

    btnRun.disabled = true;
    btnRunText.textContent = "Processando...";
    viewerPlaceholder.style.display = "none";
    interactiveStage.style.display = "none";
    renderedStage.style.display = "none";
    resultsPanel.style.display = "none";
    viewerLoading.style.display = "flex";

    const roiNote = quadratCorners ? "Recorte 4-Cantos + Homografia" : "Foto Inteira";
    loadingTitle.textContent = "Segmentando Colônias de Corais...";
    loadingSubtext.textContent = colabUrl
      ? `Filtro '${filterMode.toUpperCase()}' (${roiNote}) ➔ CoralSCOP na GPU (Grid ${pointsPerSide}x${pointsPerSide}, IoU ${predIou.toFixed(2)}, Estab. ${stabilityScore.toFixed(2)})...`
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
          quadrat_height_cm: quadratHVal,
          filter_mode: filterMode,
          quadrat_corners: quadratCorners,
          render_on_enhanced: false,
          points_per_side: pointsPerSide,
          pred_iou_thresh: predIou,
          stability_score_thresh: stabilityScore,
          crop_n_layers: cropLayers,
          crop_n_points_downscale_factor: cropDownscale
        })
      });

      const json = await resp.json();
      if (!json.success) {
        throw new Error(json.error || "Erro durante o processamento do pipeline.");
      }

      currentResult = json.data;
      renderResults(currentResult);
    } catch (err) {
      const isConnErr =
        err.message.includes("10054") ||
        err.message.includes("Conexão perdida") ||
        err.message.includes("Connection aborted");
      if (isConnErr) {
        alert(
          `🔴 Falha de Conexão com o Google Colab:\n\n` +
            `A conexão foi interrompida pelo host remoto.\n` +
            `Verifique no Colab se a Célula 6 ainda está ativa ou use NGROK_AUTHTOKEN.\n\n` +
            `Dica: Clique em "📋 Logs" no topo para diagnóstico completo.`
        );
      } else {
        alert(`Erro: ${err.message}\n\nClique em "📋 Logs" no topo para ver o histórico detalhado.`);
      }
      showImageInStage(imageName);
    } finally {
      viewerLoading.style.display = "none";
      btnRun.disabled = false;
      btnRunText.textContent = "Executar CoralSCOP ➔ CoralNet";
    }
  });

  // 7. Render Results Reprojected onto Original Photo
  function renderResults(res) {
    currentImageDimensions = { width: res.image_width, height: res.image_height };
    imageNameBadge.textContent = `${res.image_filename} (${res.image_width}x${res.image_height} px)`;
    colonyCountBadge.style.display = "inline-flex";
    colonyCountBadge.textContent = `${res.total_colonies} colônias (${res.total_coral_cover_pct || 0}% cobertura)`;

    if (res.enhanced_image_filename && res.filter_mode !== "none") {
      enhancedUrlByImage[res.image_filename] = `/output/${res.enhanced_image_filename}?t=${Date.now()}`;
    }

    // Reproject onto Original Photo by default (user can toggle enhanced bg anytime via btnToggleBg!)
    showingEnhancedBg = false;
    updateBgToggleUi();

    renderedImage.src = `/output/${res.output_image_filename}?t=${Date.now()}`;
    stageSvg.setAttribute("viewBox", `0 0 ${res.image_width} ${res.image_height}`);
    stageImage.onload = () => {
      updateQuadratUiState();
      redrawSvgScene();
    };
    stageImage.src = `/images/${res.image_filename}`;
    redrawSvgScene();

    // CSV Download Button
    btnDownloadCsv.style.display = "inline-flex";
    btnDownloadCsv.onclick = () => {
      window.location.href = `/api/download/csv/${res.output_csv_filename}`;
    };

    opacityControl.style.display = activeViewMode === "interactive" ? "flex" : "none";
    interactiveStage.style.display = activeViewMode === "interactive" ? "flex" : "none";
    renderedStage.style.display = activeViewMode === "rendered" ? "flex" : "none";

    // Results Panel
    resultsPanel.style.display = "block";
    const roiTag = res.has_quadrat_roi ? "Homografia 4-Cantos" : "Foto Inteira";
    const samInfo = res.sam_params
      ? ` | ${res.remote_model || "CoralSCOP"}: ${res.sam_params.points_per_side}x${res.sam_params.points_per_side} pts, IoU ≥ ${res.sam_params.pred_iou_thresh}, Estab. ≥ ${res.sam_params.stability_score_thresh}`
      : "";
    resultsMeta.textContent = `Cobertura Coralínea: ${res.total_coral_cm2} cm² (${res.total_coral_cover_pct}%) em ${res.quadrat_width_cm}x${res.quadrat_height_cm} cm (${roiTag}) | Filtro: ${res.filter_label || res.filter_mode} | NMS: -${res.suppressed_redundant_masks} duplicatas${samInfo}`;

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
          <div class="bar-fill" style="width: ${Math.min(100, item.coverage_pct)}%; background-color: ${item.color};"></div>
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
    const partsNote =
      col.polygons && col.polygons.length > 1 ? ` &bull; ${col.polygons.length} lóbulos unidos` : "";
    colonyTooltip.innerHTML = `
      <div class="tooltip-genus">
        <span class="tooltip-color-dot" style="background-color: ${col.color};"></span>
        #${col.id} ${col.genus}
      </div>
      <div>Área Real: <strong>${col.area_cm2} cm²</strong> (${col.area_pct}% do quadrante${partsNote})</div>
      <div>Confiança Taxonômica: <strong>${(col.confidence * 100).toFixed(1)}%</strong> &bull; Consenso: <strong>${(col.consensus_ratio * 100).toFixed(0)}%</strong></div>
      <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 2px;">${col.area_pixels.toLocaleString("pt-BR")} px &bull; ${col.sample_points_count} pontos internos</div>
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
          poly.style.strokeWidth = "6px";
          poly.style.fillOpacity = "0.78";
        } else {
          poly.style.fillOpacity = "0.08";
        }
      } else {
        poly.style.stroke = poly.getAttribute("fill");
        poly.style.strokeWidth = "3.5px";
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

  // 8. Log Viewer Modal
  const btnOpenLogs = document.getElementById("btn-open-logs");
  const btnCloseLogs = document.getElementById("btn-close-logs");
  const btnRefreshLogs = document.getElementById("btn-refresh-logs");
  const btnClearLogs = document.getElementById("btn-clear-logs");
  const btnCopyLogs = document.getElementById("btn-copy-logs");
  const logsModal = document.getElementById("logs-modal");
  const logsTerminal = document.getElementById("logs-terminal");
  const logsBody = document.getElementById("logs-body");
  const logFilePath = document.getElementById("log-file-path");

  async function fetchLogs() {
    if (!logsTerminal) return;
    try {
      const resp = await fetch("/api/logs");
      const data = await resp.json();
      if (data.log_file && logFilePath) {
        logFilePath.textContent = `Arquivo de log: ${data.log_file}`;
      }
      renderLogEntries(data.logs || []);
    } catch (err) {
      logsTerminal.innerHTML = `<div class="log-line log-error">[ERRO] Falha ao carregar logs: ${err.message}</div>`;
    }
  }

  function renderLogEntries(logs) {
    if (!logsTerminal) return;
    if (logs.length === 0) {
      logsTerminal.innerHTML = '<div class="log-line log-info">Nenhum evento registrado ainda.</div>';
      return;
    }

    logsTerminal.innerHTML = "";
    logs.forEach((item) => {
      const line = document.createElement("div");
      let levelClass = "log-info";
      if (item.level === "SUCCESS") levelClass = "log-success";
      else if (item.level === "WARNING") levelClass = "log-warning";
      else if (item.level === "ERROR") levelClass = "log-error";

      line.className = `log-line ${levelClass}`;
      line.textContent = `[${item.time || "--:--:--"}] [${item.level || "INFO"}] ${item.message}`;
      logsTerminal.appendChild(line);
    });

    if (logsBody) {
      logsBody.scrollTop = logsBody.scrollHeight;
    }
  }

  if (btnOpenLogs) {
    btnOpenLogs.addEventListener("click", () => {
      if (logsModal) {
        logsModal.style.display = "flex";
        fetchLogs();
      }
    });
  }

  if (btnCloseLogs) {
    btnCloseLogs.addEventListener("click", () => {
      if (logsModal) logsModal.style.display = "none";
    });
  }

  if (logsModal) {
    logsModal.addEventListener("click", (e) => {
      if (e.target === logsModal) {
        logsModal.style.display = "none";
      }
    });
  }

  if (btnRefreshLogs) {
    btnRefreshLogs.addEventListener("click", fetchLogs);
  }

  if (btnClearLogs) {
    btnClearLogs.addEventListener("click", async () => {
      await fetch("/api/logs/clear", { method: "POST" });
      fetchLogs();
    });
  }

  if (btnCopyLogs) {
    btnCopyLogs.addEventListener("click", () => {
      const text = Array.from(logsTerminal.querySelectorAll(".log-line"))
        .map((l) => l.textContent)
        .join("\n");
      navigator.clipboard.writeText(text).then(() => {
        btnCopyLogs.textContent = "✅ Copiado!";
        setTimeout(() => {
          btnCopyLogs.textContent = "📋 Copiar Logs";
        }, 2000);
      });
    });
  }

  // Initial load
  loadImages();
});
