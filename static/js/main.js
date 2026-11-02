// CoralSCOP + BioCLIP 2.5 ReefNet Interactive Benthic Coral Dashboard (Fase 6)
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const colabUrlInput = document.getElementById("colab-url-input");
  const btnTestColab = document.getElementById("btn-test-colab");
  const colabStatusBadge = document.getElementById("colab-status-badge");
  const colabStatusText = document.getElementById("colab-status-text");
  const bioclipStatusBadge = document.getElementById("bioclip-status-badge");
  const bioclipStatusText = document.getElementById("bioclip-status-text");

  const imageSelect = document.getElementById("image-select");
  const thumbnailStrip = document.getElementById("thumbnail-strip");
  const fileInput = document.getElementById("file-input");

  // Project Workspace & Header Elements
  const projectHeaderPill = document.getElementById("project-header-pill");
  const headerProjectName = document.getElementById("header-project-name");
  const btnOpenProjects = document.getElementById("btn-open-projects");
  const btnQuickProjects = document.getElementById("btn-quick-projects");
  const sidebarProjectType = document.getElementById("sidebar-project-type");
  const sidebarProjectName = document.getElementById("sidebar-project-name");
  const sidebarProjectPath = document.getElementById("sidebar-project-path");
  const btnDownloadProjCsv = document.getElementById("btn-download-proj-csv");

  // Batch & Status Summary Elements
  const countProcessedBadge = document.getElementById("count-processed-badge");
  const countPendingBadge = document.getElementById("count-pending-badge");
  const countMismatchBadge = document.getElementById("count-mismatch-badge");
  const btnBatchPending = document.getElementById("btn-batch-pending");
  const btnBatchSelected = document.getElementById("btn-batch-selected");
  const btnBatchAll = document.getElementById("btn-batch-all");
  const batchSelectedCount = document.getElementById("batch-selected-count");
  const activePhotoStatusBadge = document.getElementById("active-photo-status-badge");
  const chkSelectAllPhotos = document.getElementById("chk-select-all-photos");
  const photoTotalCount = document.getElementById("photo-total-count");
  const photoChecklistItems = document.getElementById("photo-checklist-items");

  // Project Manager Modal Elements
  const projectsModal = document.getElementById("projects-modal");
  const btnCloseProjects = document.getElementById("btn-close-projects");
  const btnModalCloseFooter = document.getElementById("btn-modal-close-footer");
  const recentProjectsList = document.getElementById("recent-projects-list");
  const newProjectName = document.getElementById("new-project-name");
  const newProjectRoot = document.getElementById("new-project-root");
  const btnPickFolderNew = document.getElementById("btn-pick-folder-new");
  const chkCopySamples = document.getElementById("chk-copy-samples");
  const btnCreateProjectSubmit = document.getElementById("btn-create-project-submit");
  const openProjectRoot = document.getElementById("open-project-root");
  const btnPickFolderOpen = document.getElementById("btn-pick-folder-open");
  const btnOpenProjectSubmit = document.getElementById("btn-open-project-submit");
  const btnActivateDemo = document.getElementById("btn-activate-demo");
  const activeProjectFooterLabel = document.getElementById("active-project-footer-label");

  // Batch Progress Modal Elements
  const batchProgressModal = document.getElementById("batch-progress-modal");
  const batchModalTitle = document.getElementById("batch-modal-title");
  const batchModalSubtitle = document.getElementById("batch-modal-subtitle");
  const btnCloseBatchModal = document.getElementById("btn-close-batch-modal");
  const batchProgressCount = document.getElementById("batch-progress-count");
  const batchProgressPercent = document.getElementById("batch-progress-percent");
  const batchProgressBarFill = document.getElementById("batch-progress-bar-fill");
  const batchCurrentImage = document.getElementById("batch-current-image");
  const batchChecklist = document.getElementById("batch-checklist");
  const btnCancelBatch = document.getElementById("btn-cancel-batch");
  const btnFinishBatch = document.getElementById("btn-finish-batch");

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

  // Polygon Visibility & Post-Processing Manual Draw Controls
  const polygonVisibilityControls = document.getElementById("polygon-visibility-controls");
  const btnDrawPolygon = document.getElementById("btn-draw-polygon");
  const btnTogglePolygons = document.getElementById("btn-toggle-polygons");
  const btnToggleOutline = document.getElementById("btn-toggle-outline");
  const btnToggleDiscarded = document.getElementById("btn-toggle-discarded");

  // Pan, Zoom & Fullscreen Elements
  const viewerContainer = document.getElementById("viewer-container");
  const panzoomLayer = document.getElementById("panzoom-layer");
  const renderedPanzoomLayer = document.getElementById("rendered-panzoom-layer");
  const zoomHud = document.getElementById("zoom-hud");
  const btnZoomIn = document.getElementById("btn-zoom-in");
  const btnZoomOut = document.getElementById("btn-zoom-out");
  const btnZoomReset = document.getElementById("btn-zoom-reset");
  const btnFullscreenCanvas = document.getElementById("btn-fullscreen-canvas");

  // Multi-Select Banner
  const multiselectBanner = document.getElementById("multiselect-banner");
  const multiselectBannerText = document.getElementById("multiselect-banner-text");
  const btnDoneMultiselect = document.getElementById("btn-done-multiselect");

  // Post-Processing Manual Polygon Demarcation Drawer Elements
  const manualDrawCard = document.getElementById("manual-draw-card");
  const manualDrawColorDot = document.getElementById("manual-draw-color-dot");
  const manualDrawMetrics = document.getElementById("manual-draw-metrics");
  const manualDrawGenusSelect = document.getElementById("manual-draw-genus-select");
  const manualDrawBioclipNote = document.getElementById("manual-draw-bioclip-note");
  const btnCloseManualDraw = document.getElementById("btn-close-manual-draw");
  const btnSaveManualDraw = document.getElementById("btn-save-manual-draw");
  const btnUndoManualVertex = document.getElementById("btn-undo-manual-vertex");
  const btnCancelManualDraw = document.getElementById("btn-cancel-manual-draw");

  // Few-Shot Controls
  const chkFewshotEnabled = document.getElementById("chk-fewshot-enabled");
  const fewshotStatusPill = document.getElementById("fewshot-status-pill");
  const fewshotGeneraChips = document.getElementById("fewshot-genera-chips");
  const fewshotActionsRow = document.getElementById("fewshot-actions-row");
  const btnReclassifyPhoto = document.getElementById("btn-reclassify-photo");
  const btnClearFewshot = document.getElementById("btn-clear-fewshot");

  // Interactive Colony Inspector / Grouping / Sub-Part / Vertex Editor Elements
  const colonyEditorCard = document.getElementById("colony-editor-card");
  const editorColorDot = document.getElementById("editor-color-dot");
  const editorColonyTitle = document.getElementById("editor-colony-title");
  const editorSinglePane = document.getElementById("editor-single-pane");
  const editorGroupPane = document.getElementById("editor-group-pane");
  const editorVertexPane = document.getElementById("editor-vertex-pane");
  const editorColonyMetrics = document.getElementById("editor-colony-metrics");
  const editorColonySource = document.getElementById("editor-colony-source");
  const editorAltChips = document.getElementById("editor-alt-chips");
  const editorGenusSelect = document.getElementById("editor-genus-select");
  const btnCloseEditor = document.getElementById("btn-close-editor");
  const editorActiveActions = document.getElementById("editor-active-actions");
  const editorDiscardedActions = document.getElementById("editor-discarded-actions");
  const btnEditorRestore = document.getElementById("btn-editor-restore");
  const btnEditorTeach = document.getElementById("btn-editor-teach");
  const btnEditorSaveOnly = document.getElementById("btn-editor-save-only");
  const btnEditorDelete = document.getElementById("btn-editor-delete");
  const btnStartVertexEdit = document.getElementById("btn-start-vertex-edit");
  const btnStartGroupSelect = document.getElementById("btn-start-group-select");

  // Existing Polygon Vertex Editor Controls
  const vertexEditMetrics = document.getElementById("vertex-edit-metrics");
  const chkRefreshBioclip = document.getElementById("chk-refresh-bioclip");
  const btnSaveVertexEdit = document.getElementById("btn-save-vertex-edit");
  const btnUndoVertexEdit = document.getElementById("btn-undo-vertex-edit");
  const btnCancelVertexEdit = document.getElementById("btn-cancel-vertex-edit");

  // Sub-polygon Group Part Controls
  const editorPartsBox = document.getElementById("editor-parts-box");
  const editorPartsTitle = document.getElementById("editor-parts-title");
  const editorPartsChips = document.getElementById("editor-parts-chips");
  const btnPartSplit = document.getElementById("btn-part-split");
  const btnPartDiscard = document.getElementById("btn-part-discard");
  const btnGroupExplode = document.getElementById("btn-group-explode");

  // Multi-selection Grouping Pane Controls
  const groupSelectedSummary = document.getElementById("group-selected-summary");
  const groupSelectedList = document.getElementById("group-selected-list");
  const groupGenusWarning = document.getElementById("group-genus-warning");
  const btnConfirmGroup = document.getElementById("btn-confirm-group");
  const btnToggleAddMore = document.getElementById("btn-toggle-add-more");
  const btnCancelGroupSelect = document.getElementById("btn-cancel-group-select");
  const editorFeedbackMsg = document.getElementById("editor-feedback-msg");

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

  // Footer Tables (Per Colony/Group vs Consolidated Per Genus)
  const btnTableGroups = document.getElementById("btn-table-groups");
  const btnTableGenera = document.getElementById("btn-table-genera");
  const groupsTableWrapper = document.getElementById("groups-table-wrapper");
  const generaTableWrapper = document.getElementById("genera-table-wrapper");
  const groupsTbody = document.getElementById("groups-tbody");
  const groupsTfoot = document.getElementById("groups-tfoot");
  const speciesTbody = document.getElementById("species-tbody");

  // Application State
  let coralGenera = [
    "Montastraea", "Mussismilia", "Porites", "Siderastrea", "Agaricia",
    "Millepora", "Madracis", "Meandrina", "Stephanocoenia", "Scolymia", "Favia"
  ];
  let nonCoralLabel = "__NON_CORAL__";
  let nonCoralDisplay = "Não é Coral (Descartar)";
  let classColors = {};
  let currentResult = null;

  // Workspace & Batch Processing State
  let activeWorkspace = null;
  let workspaceImages = [];
  const selectedForBatch = new Set();
  let isBatchRunning = false;

  // Selection, Grouping & Visibility State
  let selectedColonyId = null;
  let selectedPartIndex = 0;
  let groupSelectionIds = [];
  let isMultiSelectMode = false;
  let pendingGroupReturnIds = null;

  let polygonsVisible = true;
  let outlineOnlyMode = false;
  let showDiscardedPolygons = false;
  let activeFooterTab = "groups";

  let activeViewMode = "interactive";
  let currentImageDimensions = { width: 4000, height: 3000 };
  const quadratCornersByImage = {};
  const enhancedUrlByImage = {};
  let showingEnhancedBg = false;

  // Quadrat Picking / Dragging State
  let isPickingQuadrat = false;
  let pickingCorners = [];
  let draggingCornerIdx = null;

  // Post-Processing Manual Polygon Drawing State
  let isDrawingManualPolygon = false;
  let manualDrawPoints = [];
  let manualHoverPoint = null;
  let isFreehandLassoActive = false;
  let isSavingManualPolygon = false;

  // Post-Processing Existing Polygon Vertex Editing State
  let isEditingVertices = false;
  let editingVertices = [];
  let vertexUndoStack = [];
  let draggingVertexIdx = null;
  let isSavingVertexEdit = false;

  // Pan, Zoom & Fullscreen State (Unrestricted drag + cursor-centered wheel zoom)
  const MIN_ZOOM = 0.35;
  const MAX_ZOOM = 12.0;
  let zoomLevel = 1.0;
  let panX = 0;
  let panY = 0;
  let isCanvasFullscreen = false;
  let isPointerDownForPan = false;
  let didDragDuringPan = false;
  let panStartClient = { x: 0, y: 0 };
  let panStartOffset = { x: 0, y: 0 };
  let suppressClickUntil = 0;

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

  // =========================================================================
  // 1. PAN, ZOOM & FULLSCREEN ENGINE (1:1 Locked Image + SVG, Unrestricted Drag)
  // =========================================================================
  function applyPanZoomTransform() {
    const tf = `translate(${panX}px, ${panY}px) scale(${zoomLevel})`;
    if (panzoomLayer) panzoomLayer.style.transform = tf;
    if (renderedPanzoomLayer) renderedPanzoomLayer.style.transform = tf;
    if (btnZoomReset) {
      btnZoomReset.textContent = `${Math.round(zoomLevel * 100)}%`;
    }
    if (isDrawingManualPolygon) {
      renderManualDrawOverlay();
    }
    if (isEditingVertices) {
      renderVertexEditOverlay();
    }
  }

  function resetPanZoom() {
    zoomLevel = 1.0;
    panX = 0;
    panY = 0;
    applyPanZoomTransform();
  }

  function toggleFullscreenCanvas(forceState = null) {
    if (!viewerContainer) return;
    isCanvasFullscreen = forceState !== null ? Boolean(forceState) : !isCanvasFullscreen;
    viewerContainer.classList.toggle("canvas-fullscreen", isCanvasFullscreen);
    if (btnFullscreenCanvas) {
      btnFullscreenCanvas.textContent = isCanvasFullscreen ? "🗗 Sair Tela Cheia" : "⛶ Tela Cheia";
      btnFullscreenCanvas.classList.toggle("active", isCanvasFullscreen);
    }
  }

  if (btnFullscreenCanvas) {
    btnFullscreenCanvas.addEventListener("click", () => toggleFullscreenCanvas());
  }

  function zoomAtScreenPoint(targetZoom, clientX, clientY) {
    if (!viewerContainer) return;
    const clamped = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, targetZoom));
    const rect = viewerContainer.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const ux = clientX - cx;
    const uy = clientY - cy;
    const ratio = clamped / zoomLevel;

    panX = ux - ratio * (ux - panX);
    panY = uy - ratio * (uy - panY);
    zoomLevel = clamped;
    applyPanZoomTransform();
  }

  if (viewerContainer) {
    // Capture-phase click blocker right after a drag-pan or lasso gesture
    viewerContainer.addEventListener(
      "click",
      (e) => {
        if (performance.now() < suppressClickUntil) {
          e.stopPropagation();
          e.preventDefault();
        }
      },
      true
    );

    // Smooth cursor-centered mouse wheel zoom
    viewerContainer.addEventListener(
      "wheel",
      (e) => {
        if (e.target.closest("#colony-editor-card, #manual-draw-card")) {
          return; // allow normal scrolling inside floating drawers
        }
        if (viewerPlaceholder && viewerPlaceholder.style.display !== "none") {
          return;
        }
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.16 : 1 / 1.16;
        zoomAtScreenPoint(zoomLevel * factor, e.clientX, e.clientY);
      },
      { passive: false }
    );

    // Unrestricted click-and-drag panning across & outside canvas bounds (+ Shift+Drag Lasso in Manual Draw)
    viewerContainer.addEventListener("mousedown", (e) => {
      if (e.button !== 0 && e.button !== 1) return;
      if (
        e.target.closest(
          "#colony-editor-card, #manual-draw-card, #zoom-hud, #quadrat-banner, #multiselect-banner"
        )
      ) {
        return;
      }
      if (draggingCornerIdx !== null || draggingVertexIdx !== null) return;
      if (viewerPlaceholder && viewerPlaceholder.style.display !== "none") return;

      // In Manual Polygon Drawing mode, Shift + Left Drag traces a smooth freehand lasso contour!
      if (isDrawingManualPolygon && e.button === 0 && e.shiftKey) {
        e.preventDefault();
        isFreehandLassoActive = true;
        const pt = clientToSvgCoords(e);
        if (
          manualDrawPoints.length === 0 ||
          Math.hypot(
            pt[0] - manualDrawPoints[manualDrawPoints.length - 1][0],
            pt[1] - manualDrawPoints[manualDrawPoints.length - 1][1]
          ) >= 4
        ) {
          manualDrawPoints.push(pt);
          updateManualDrawUi();
          renderManualDrawOverlay();
        }
        return;
      }

      isPointerDownForPan = true;
      didDragDuringPan = false;
      panStartClient = { x: e.clientX, y: e.clientY };
      panStartOffset = { x: panX, y: panY };
    });
  }

  if (btnZoomIn) {
    btnZoomIn.addEventListener("click", () => {
      const rect = viewerContainer.getBoundingClientRect();
      zoomAtScreenPoint(zoomLevel * 1.25, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
  }

  if (btnZoomOut) {
    btnZoomOut.addEventListener("click", () => {
      const rect = viewerContainer.getBoundingClientRect();
      zoomAtScreenPoint(zoomLevel / 1.25, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
  }

  if (btnZoomReset) {
    btnZoomReset.addEventListener("click", resetPanZoom);
  }

  // Exact screen-to-image coordinate conversion under any translate() + scale()
  function clientToSvgCoords(evt) {
    const rect = stageImage.getBoundingClientRect();
    const rx = (evt.clientX - rect.left) / Math.max(1, rect.width);
    const ry = (evt.clientY - rect.top) / Math.max(1, rect.height);
    return [
      Math.max(0, Math.min(currentImageDimensions.width, Math.round(rx * currentImageDimensions.width))),
      Math.max(0, Math.min(currentImageDimensions.height, Math.round(ry * currentImageDimensions.height)))
    ];
  }

  // =========================================================================
  // 2. TAXONOMY DROPDOWN (11 CORAL GENERA + NON-CORAL) & FEW-SHOT SUMMARY
  // =========================================================================
  function syncManualDrawColorDot() {
    if (!manualDrawColorDot || !manualDrawGenusSelect) return;
    const val = manualDrawGenusSelect.value;
    if (val === "__AUTO_BIOCLIP__") {
      manualDrawColorDot.style.backgroundColor = "#10b981";
    } else {
      manualDrawColorDot.style.backgroundColor = classColors[val] || "#38bdf8";
    }
    if (isDrawingManualPolygon) {
      renderManualDrawOverlay();
    }
  }

  if (manualDrawGenusSelect) {
    manualDrawGenusSelect.addEventListener("change", syncManualDrawColorDot);
  }

  function populateGenusSelect() {
    if (editorGenusSelect) {
      editorGenusSelect.innerHTML = "";

      const grpCorals = document.createElement("optgroup");
      grpCorals.label = "Gêneros de Corais (11)";
      coralGenera.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = g;
        opt.textContent = g;
        grpCorals.appendChild(opt);
      });
      editorGenusSelect.appendChild(grpCorals);

      const grpNonCoral = document.createElement("optgroup");
      grpNonCoral.label = "Descarte / Filtro Negativo";
      const ncOpt = document.createElement("option");
      ncOpt.value = nonCoralLabel;
      ncOpt.textContent = `🚫 ${nonCoralDisplay}`;
      grpNonCoral.appendChild(ncOpt);
      editorGenusSelect.appendChild(grpNonCoral);
    }

    if (manualDrawGenusSelect) {
      const prevVal = manualDrawGenusSelect.value;
      manualDrawGenusSelect.innerHTML = "";

      const grpAuto = document.createElement("optgroup");
      grpAuto.label = "Classificação Automática (GPU)";
      const autoOpt = document.createElement("option");
      autoOpt.value = "__AUTO_BIOCLIP__";
      autoOpt.textContent = "🤖 Auto-classificar com BioCLIP 2.5 (Colab)";
      grpAuto.appendChild(autoOpt);
      manualDrawGenusSelect.appendChild(grpAuto);

      const grpManualCorals = document.createElement("optgroup");
      grpManualCorals.label = "Escolher Gênero Coralíneo (11)";
      coralGenera.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = g;
        opt.textContent = g;
        grpManualCorals.appendChild(opt);
      });
      manualDrawGenusSelect.appendChild(grpManualCorals);

      if (prevVal && (prevVal === "__AUTO_BIOCLIP__" || coralGenera.includes(prevVal))) {
        manualDrawGenusSelect.value = prevVal;
      } else {
        const hasColab = Boolean(colabUrlInput && colabUrlInput.value.trim());
        manualDrawGenusSelect.value = hasColab ? "__AUTO_BIOCLIP__" : coralGenera[0];
      }
      syncManualDrawColorDot();
    }
  }

  function renderFewshotSummary(fs) {
    if (!fs) return;
    if (chkFewshotEnabled) {
      chkFewshotEnabled.checked = Boolean(fs.enabled);
    }

    const total = fs.total_samples || 0;
    if (fewshotStatusPill) {
      if (fs.enabled && total > 0) {
        fewshotStatusPill.className = "roi-status-pill roi-active";
        fewshotStatusPill.textContent = `Ativo (${total} ref)`;
      } else if (!fs.enabled && total > 0) {
        fewshotStatusPill.className = "roi-status-pill roi-picking";
        fewshotStatusPill.textContent = `Pausado (${total} ref)`;
      } else {
        fewshotStatusPill.className = "roi-status-pill roi-inactive";
        fewshotStatusPill.textContent = "Zero-Shot Puro";
      }
    }

    if (fewshotGeneraChips) {
      if (total === 0) {
        fewshotGeneraChips.innerHTML =
          '<span class="fewshot-empty-note">Modo 100% automático (BioCLIP 2.5 ReefNet — somente gêneros de corais). Clique em qualquer polígono no mapa se quiser ensinar um gênero ou filtrar "Não é Coral".</span>';
      } else {
        fewshotGeneraChips.innerHTML = "";
        (fs.by_genus || []).forEach((item) => {
          const chip = document.createElement("span");
          chip.className = "fewshot-genus-chip";
          const displayLabel = item.label || (item.genus === nonCoralLabel ? "Não é Coral" : item.genus);
          chip.innerHTML = `<span class="tooltip-color-dot" style="background-color:${item.color};"></span>${displayLabel}: ${item.count}`;
          fewshotGeneraChips.appendChild(chip);
        });
      }
    }

    if (fewshotActionsRow) {
      fewshotActionsRow.style.display = total > 0 ? "flex" : "none";
    }
  }

  async function loadTaxonomyAndFewshot() {
    try {
      const resp = await fetch("/api/taxonomy");
      const data = await resp.json();
      if (data.genera && data.genera.length > 0) {
        coralGenera = data.genera;
      }
      if (data.non_coral_label) {
        nonCoralLabel = data.non_coral_label;
      }
      if (data.non_coral_display) {
        nonCoralDisplay = data.non_coral_display;
      }
      if (data.class_colors) {
        classColors = data.class_colors;
      }
      populateGenusSelect();
      if (data.fewshot) {
        renderFewshotSummary(data.fewshot);
      }
    } catch (err) {
      populateGenusSelect();
    }
  }

  // Canonical ordering [TL, TR, BR, BL]
  function orderQuadCornersJs(pts) {
    if (!pts || pts.length !== 4) return pts;
    const copy = pts.map((p) => [p[0], p[1]]);
    copy.sort((a, b) => a[1] - b[1]);
    const topPair = copy.slice(0, 2).sort((a, b) => a[0] - b[0]);
    const botPair = copy.slice(2, 4).sort((a, b) => a[0] - b[0]);
    return [topPair[0], topPair[1], botPair[1], botPair[0]];
  }

  // =========================================================================
  // 3. POLYGON VISIBILITY CONTROLS & KEYBOARD SHORTCUTS
  // =========================================================================
  function updateVisibilityControlsUi() {
    const imgName = imageSelect ? imageSelect.value : "";
    const hasOpenSession =
      Boolean(currentResult && currentResult.image_filename === imgName) &&
      activeViewMode === "interactive";

    if (polygonVisibilityControls) {
      polygonVisibilityControls.style.display = hasOpenSession ? "inline-flex" : "none";
    }
    if (!hasOpenSession) return;

    if (btnDrawPolygon) {
      btnDrawPolygon.textContent = isDrawingManualPolygon ? "✏️ Desenhando..." : "➕ Novo Polígono";
      btnDrawPolygon.classList.toggle("btn-vis-active", isDrawingManualPolygon);
    }

    if (btnTogglePolygons) {
      btnTogglePolygons.textContent = polygonsVisible ? "👁️ Polígonos" : "🙈 Ocultos";
      btnTogglePolygons.classList.toggle("btn-vis-off", !polygonsVisible);
    }

    if (btnToggleOutline) {
      btnToggleOutline.textContent = outlineOnlyMode ? "⭕ Só Contorno: ON" : "⭕ Só Contorno";
      btnToggleOutline.classList.toggle("btn-vis-active", outlineOnlyMode);
    }

    if (btnToggleDiscarded) {
      const discCount = currentResult.discarded_count || 0;
      if (discCount > 0) {
        btnToggleDiscarded.style.display = "inline-flex";
        btnToggleDiscarded.textContent = showDiscardedPolygons
          ? `👁️ Não-Coral (${discCount})`
          : `🚫 Não-Coral (${discCount})`;
        btnToggleDiscarded.classList.toggle("btn-vis-active", showDiscardedPolygons);
      } else {
        btnToggleDiscarded.style.display = "none";
      }
    }
  }

  if (btnTogglePolygons) {
    btnTogglePolygons.addEventListener("click", () => {
      polygonsVisible = !polygonsVisible;
      updateVisibilityControlsUi();
      redrawSvgScene();
    });
  }

  if (btnToggleOutline) {
    btnToggleOutline.addEventListener("click", () => {
      outlineOnlyMode = !outlineOnlyMode;
      if (outlineOnlyMode && !polygonsVisible) {
        polygonsVisible = true;
      }
      updateVisibilityControlsUi();
      redrawSvgScene();
    });
  }

  if (btnToggleDiscarded) {
    btnToggleDiscarded.addEventListener("click", () => {
      showDiscardedPolygons = !showDiscardedPolygons;
      if (showDiscardedPolygons && !polygonsVisible) {
        polygonsVisible = true;
      }
      updateVisibilityControlsUi();
      redrawSvgScene();
    });
  }

  window.addEventListener("keydown", (e) => {
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;

    // Undo shortcuts (Ctrl+Z or Backspace) during manual drawing or vertex editing
    if (e.key === "Backspace" || ((e.ctrlKey || e.metaKey) && (e.key === "z" || e.key === "Z"))) {
      if (isDrawingManualPolygon && manualDrawPoints.length > 0) {
        e.preventDefault();
        undoLastManualVertex();
        return;
      }
      if (isEditingVertices && vertexUndoStack.length > 0) {
        e.preventDefault();
        undoVertexEditStep();
        return;
      }
    }

    // Enter saves manual polygon (>=3 vertices) or active vertex edit
    if (e.key === "Enter") {
      if (isDrawingManualPolygon && manualDrawPoints.length >= 3) {
        e.preventDefault();
        saveManualPolygon();
        return;
      }
      if (isEditingVertices && editingVertices.length >= 3) {
        e.preventDefault();
        saveVertexEdit();
        return;
      }
    }

    if (e.key === "v" || e.key === "V") {
      if (currentResult && activeViewMode === "interactive") {
        polygonsVisible = !polygonsVisible;
        updateVisibilityControlsUi();
        redrawSvgScene();
      }
    } else if (e.key === "o" || e.key === "O") {
      if (currentResult && activeViewMode === "interactive") {
        outlineOnlyMode = !outlineOnlyMode;
        if (outlineOnlyMode) polygonsVisible = true;
        updateVisibilityControlsUi();
        redrawSvgScene();
      }
    } else if (e.key === "n" || e.key === "N") {
      if (
        currentResult &&
        imageSelect &&
        currentResult.image_filename === imageSelect.value &&
        activeViewMode === "interactive"
      ) {
        e.preventDefault();
        if (isDrawingManualPolygon) {
          exitManualDrawMode();
        } else {
          startManualDrawMode();
        }
      }
    } else if (e.key === "e" || e.key === "E") {
      if (
        currentResult &&
        selectedColonyId !== null &&
        !isEditingVertices &&
        !isDrawingManualPolygon &&
        activeViewMode === "interactive"
      ) {
        e.preventDefault();
        startVertexEditMode();
      }
    } else if (e.key === "f" || e.key === "F") {
      if (viewerPlaceholder && viewerPlaceholder.style.display === "none") {
        e.preventDefault();
        toggleFullscreenCanvas();
      }
    } else if (e.key === "0") {
      resetPanZoom();
    } else if (e.key === "Escape") {
      if (isDrawingManualPolygon) {
        exitManualDrawMode();
      } else if (isEditingVertices) {
        cancelVertexEditMode();
      } else if (isPickingQuadrat) {
        isPickingQuadrat = false;
        pickingCorners = [];
        updateQuadratUiState();
        redrawSvgScene();
      } else if (isMultiSelectMode) {
        isMultiSelectMode = false;
        updateMultiselectBannerUi();
      } else if (colonyEditorCard && colonyEditorCard.style.display !== "none") {
        closeColonyEditor();
      } else if (isCanvasFullscreen) {
        toggleFullscreenCanvas(false);
      }
    }
  });

  // =========================================================================
  // 4. SLIDERS, SCALE & ACCORDION HYPERPARAMETERS
  // =========================================================================
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

  if (toggleSamParams && samParamsContent) {
    toggleSamParams.addEventListener("click", () => {
      const isHidden = samParamsContent.style.display === "none";
      samParamsContent.style.display = isHidden ? "block" : "none";
      if (samAccordionArrow) {
        samAccordionArrow.classList.toggle("open", isHidden);
      }
    });
  }

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

  function updateColabStatusDot(status) {
    const dot = document.getElementById("colab-status-dot");
    if (!dot) return;
    dot.className = "tab-status-dot";
    if (status === "online") {
      dot.classList.add("dot-online");
      dot.title = "Colab Online (GPU Conectada)";
    } else if (status === "busy" || status === "warning") {
      dot.classList.add("dot-busy");
      dot.title = "Colab Ocupado / Atenção";
    } else {
      dot.classList.add("dot-offline");
      dot.title = "Colab Desconectado";
    }
  }

  // =========================================================================
  // 5. COLAB GPU HEALTH CHECK
  // =========================================================================
  async function testColabConnection() {
    const url = colabUrlInput.value.trim();
    if (!url) {
      colabStatusBadge.className = "badge badge-offline";
      colabStatusText.textContent = "Colab GPU: Nenhuma URL";
      updateColabStatusDot("offline");
      return;
    }

    localStorage.setItem("coralscop_colab_url", url);
    colabStatusText.textContent = "Verificando...";
    btnTestColab.disabled = true;
    updateColabStatusDot("busy");

    try {
      const resp = await fetch("/api/test-colab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ colab_url: url })
      });
      const data = await resp.json();

      if (data.connected) {
        if (data.is_coralscop && data.has_bioclip) {
          colabStatusBadge.className = "badge badge-online";
          colabStatusText.textContent = `🟢 CoralSCOP + BioCLIP Online (${data.gpu_name || "Tesla T4"})`;
          updateColabStatusDot("online");
          if (bioclipStatusBadge && bioclipStatusText) {
            bioclipStatusBadge.className = "badge badge-online";
            bioclipStatusText.textContent = `🧬 ${data.classifier_model || "BioCLIP 2.5 ReefNet"}`;
          }
        } else if (data.is_coralscop && !data.has_bioclip) {
          colabStatusBadge.className = "badge badge-warning";
          colabStatusText.textContent = "🟡 CoralSCOP sem BioCLIP (Atualize o notebook no Colab)";
          updateColabStatusDot("warning");
          if (bioclipStatusBadge && bioclipStatusText) {
            bioclipStatusBadge.className = "badge badge-warning";
            bioclipStatusText.textContent = "Atualize o Colab p/ BioCLIP 2.5";
          }
        } else {
          colabStatusBadge.className = "badge badge-warning";
          colabStatusText.textContent = `🟡 ${data.model || "Servidor Antigo"} (Atualize o Colab)`;
          updateColabStatusDot("warning");
        }
      } else {
        colabStatusBadge.className = "badge badge-offline";
        colabStatusText.textContent = "🔴 Servidor Inacessível";
        updateColabStatusDot("offline");
      }
    } catch (err) {
      colabStatusBadge.className = "badge badge-offline";
      colabStatusText.textContent = "🔴 Erro de Conexão";
      updateColabStatusDot("offline");
    } finally {
      btnTestColab.disabled = false;
    }
  }

  btnTestColab.addEventListener("click", testColabConnection);
  if (colabUrlInput.value) {
    setTimeout(testColabConnection, 400);
  }

  // =========================================================================
  // 6. COLONY INSPECTOR, NON-CORAL FILTERING, GROUPING & SUB-PART REMOVAL
  // =========================================================================
  function updateMultiselectBannerUi() {
    if (!multiselectBanner) return;
    if (isMultiSelectMode) {
      multiselectBanner.style.display = "flex";
      const count = groupSelectionIds.length;
      multiselectBannerText.textContent = `🔗 Modo Agrupar (${count} selecionado${count === 1 ? "" : "s"}): clique em outros polígonos para adicioná-los ao grupo...`;
    } else {
      multiselectBanner.style.display = "none";
    }
    if (btnToggleAddMore) {
      btnToggleAddMore.textContent = isMultiSelectMode ? "✅ Parar de Clicar" : "➕ Clicar em Mais";
      btnToggleAddMore.classList.toggle("btn-vis-active", isMultiSelectMode);
    }
  }

  function clearVertexEditLayer() {
    const layer = document.getElementById("vertex-edit-layer");
    if (layer) layer.remove();
  }

  function clearManualDrawLayer() {
    const layer = document.getElementById("manual-draw-layer");
    if (layer) layer.remove();
  }

  function syncPolygonSelectionHighlights() {
    const multiSet = new Set(groupSelectionIds);
    document.querySelectorAll(".colony-polygon").forEach((el) => {
      const cid = parseInt(el.getAttribute("data-id"), 10);
      const pidx = parseInt(el.getAttribute("data-part-idx") || "0", 10);
      const totalParts = parseInt(el.getAttribute("data-total-parts") || "1", 10);

      const isMulti = multiSet.size >= 2 && multiSet.has(cid);
      const isSingle = multiSet.size < 2 && selectedColonyId === cid;
      const isSubpart = isSingle && totalParts >= 2 && pidx === selectedPartIndex;
      const isBeingEdited = isEditingVertices && selectedColonyId === cid && pidx === selectedPartIndex;

      el.classList.toggle("group-selected-colony", isMulti);
      el.classList.toggle("selected-colony", isSingle && !isBeingEdited);
      el.classList.toggle("selected-subpart", isSubpart && !isBeingEdited);
      el.classList.toggle("being-vertex-edited", isBeingEdited);
    });
  }

  function closeColonyEditor() {
    if (isEditingVertices) {
      isEditingVertices = false;
      editingVertices = [];
      vertexUndoStack = [];
      draggingVertexIdx = null;
      clearVertexEditLayer();
    }
    selectedColonyId = null;
    selectedPartIndex = 0;
    groupSelectionIds = [];
    isMultiSelectMode = false;
    pendingGroupReturnIds = null;
    updateMultiselectBannerUi();
    if (colonyEditorCard) colonyEditorCard.style.display = "none";
    if (editorFeedbackMsg) editorFeedbackMsg.style.display = "none";
    syncPolygonSelectionHighlights();
  }

  function openGroupInspector(feedbackText = null) {
    if (!currentResult || !colonyEditorCard) return;
    if (isDrawingManualPolygon) exitManualDrawMode();
    if (isEditingVertices) {
      isEditingVertices = false;
      editingVertices = [];
      vertexUndoStack = [];
      draggingVertexIdx = null;
      clearVertexEditLayer();
    }
    hideTooltip();

    // Filter to valid, non-discarded colonies
    groupSelectionIds = groupSelectionIds.filter((cid) => {
      const c = currentResult.colonies.find((x) => x.id === cid);
      return Boolean(c && !c.discarded);
    });

    if (groupSelectionIds.length === 0) {
      closeColonyEditor();
      return;
    }
    if (groupSelectionIds.length === 1 && !isMultiSelectMode) {
      const singleCol = currentResult.colonies.find((x) => x.id === groupSelectionIds[0]);
      groupSelectionIds = [];
      openColonyEditor(singleCol, 0, feedbackText);
      return;
    }

    selectedColonyId = null;
    if (editorSinglePane) editorSinglePane.style.display = "none";
    if (editorVertexPane) editorVertexPane.style.display = "none";
    if (editorGroupPane) editorGroupPane.style.display = "block";

    const selectedCols = groupSelectionIds
      .map((cid) => currentResult.colonies.find((x) => x.id === cid))
      .filter(Boolean);

    const distinctGenera = Array.from(new Set(selectedCols.map((c) => c.genus)));
    const totalCm2 = selectedCols.reduce((acc, c) => acc + (c.area_cm2 || 0), 0);
    const totalPct = selectedCols.reduce((acc, c) => acc + (c.area_pct || 0), 0);
    const totalParts = selectedCols.reduce(
      (acc, c) => acc + ((c.polygons && c.polygons.length) || 1),
      0
    );

    if (editorColorDot) {
      editorColorDot.style.backgroundColor =
        distinctGenera.length === 1 ? selectedCols[0].color : "#fbbf24";
    }
    if (editorColonyTitle) {
      editorColonyTitle.textContent = `Agrupar Polígonos (${selectedCols.length})`;
    }
    if (groupSelectedSummary) {
      groupSelectedSummary.innerHTML = `Total combinado: <strong>${totalCm2.toFixed(2)} cm²</strong> (${totalPct.toFixed(2)}%) &bull; <strong>${totalParts}</strong> polígonos`;
    }

    if (groupSelectedList) {
      groupSelectedList.innerHTML = "";
      selectedCols.forEach((c) => {
        const row = document.createElement("div");
        row.className = "group-item-pill";

        const left = document.createElement("div");
        left.className = "group-item-pill-left";
        left.title = "Clique para inspecionar ou corrigir o gênero deste polígono antes de agrupar";
        const pCount = (c.polygons && c.polygons.length) || 1;
        const pNote = pCount > 1 ? ` (${pCount}p)` : "";
        left.innerHTML = `<span class="tooltip-color-dot" style="background-color:${c.color};"></span><strong>#${c.id}${pNote}</strong> ${c.genus} <span style="color:#94a3b8;">(${c.area_cm2} cm²)</span>`;
        left.addEventListener("click", () => {
          // Remember group selection so after user fixes this polygon's genus, we return directly to grouping!
          pendingGroupReturnIds = [...groupSelectionIds];
          isMultiSelectMode = false;
          updateMultiselectBannerUi();
          groupSelectionIds = [];
          openColonyEditor(
            c,
            0,
            "Corrija o gênero abaixo ('✏️ Apenas Corrigir' ou '🧠 Ensinar BioCLIP') para voltar ao agrupamento."
          );
        });

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "group-item-remove";
        removeBtn.title = "Remover da seleção";
        removeBtn.innerHTML = "&times;";
        removeBtn.addEventListener("click", () => {
          groupSelectionIds = groupSelectionIds.filter((id) => id !== c.id);
          openGroupInspector();
        });

        row.appendChild(left);
        row.appendChild(removeBtn);
        groupSelectedList.appendChild(row);
      });
    }

    if (groupGenusWarning && btnConfirmGroup) {
      if (selectedCols.length < 2) {
        groupGenusWarning.style.display = "block";
        groupGenusWarning.className = "group-genus-warning";
        groupGenusWarning.textContent =
          "Clique em pelo menos mais 1 polígono do mesmo gênero no mapa para formar uma colônia agrupada.";
        btnConfirmGroup.disabled = true;
        btnConfirmGroup.textContent = "🔗 Selecione +1 Polígono";
      } else if (distinctGenera.length > 1) {
        groupGenusWarning.style.display = "block";
        groupGenusWarning.className = "group-genus-warning";
        groupGenusWarning.innerHTML = `⚠️ <strong>Gêneros diferentes (${distinctGenera.join(", ")}):</strong> clique no polígono divergente na lista acima para corrigir seu gênero (via <em>✏️ Apenas Corrigir</em> ou <em>🧠 Ensinar BioCLIP</em>) antes de agrupar.`;
        btnConfirmGroup.disabled = true;
        btnConfirmGroup.textContent = "🔒 Unifique o Gênero Primeiro";
      } else {
        const g = distinctGenera[0];
        groupGenusWarning.style.display = "block";
        groupGenusWarning.className = "group-genus-ok";
        groupGenusWarning.innerHTML = `✅ Todos classificados como <strong>${g}</strong>. Prontos para unir em 1 colônia!`;
        btnConfirmGroup.disabled = false;
        btnConfirmGroup.textContent = `🔗 Agrupar ${selectedCols.length} em 1 Colônia (${g})`;
      }
    }

    if (editorFeedbackMsg) {
      if (feedbackText) {
        editorFeedbackMsg.textContent = feedbackText;
        editorFeedbackMsg.style.display = "block";
      } else {
        editorFeedbackMsg.style.display = "none";
      }
    }

    updateMultiselectBannerUi();
    syncPolygonSelectionHighlights();
    colonyEditorCard.style.display = "block";
  }

  function renderSubpartsBox(col) {
    if (!editorPartsBox) return;
    const polys = (col && col.polygons) || [];
    if (btnStartVertexEdit) {
      btnStartVertexEdit.textContent =
        polys.length >= 2
          ? `✒️ Editar Borda da Parte #${Math.min(selectedPartIndex, polys.length - 1) + 1}`
          : "✒️ Editar Borda / Vértices";
    }
    if (!col || col.discarded || polys.length < 2) {
      editorPartsBox.style.display = "none";
      return;
    }

    if (selectedPartIndex >= polys.length || selectedPartIndex < 0) {
      selectedPartIndex = 0;
    }

    editorPartsBox.style.display = "block";
    if (editorPartsTitle) {
      editorPartsTitle.textContent = `🔗 Polígonos deste Grupo (${polys.length} partes)`;
    }

    if (editorPartsChips) {
      editorPartsChips.innerHTML = "";
      polys.forEach((_, idx) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = `part-chip ${idx === selectedPartIndex ? "active" : ""}`;
        chip.textContent = `Parte #${idx + 1}`;
        chip.addEventListener("click", () => {
          selectedPartIndex = idx;
          renderSubpartsBox(col);
          syncPolygonSelectionHighlights();
        });
        editorPartsChips.appendChild(chip);
      });
    }

    if (btnPartSplit) {
      btnPartSplit.textContent = `✂️ Separar Parte #${selectedPartIndex + 1}`;
    }
    if (btnPartDiscard) {
      btnPartDiscard.textContent = `🗑️ Descartar Parte #${selectedPartIndex + 1}`;
    }
  }

  function openColonyEditor(col, partIdx = 0, feedbackText = null) {
    if (!col || !colonyEditorCard) return;
    if (isDrawingManualPolygon) exitManualDrawMode();
    if (isEditingVertices) {
      isEditingVertices = false;
      editingVertices = [];
      vertexUndoStack = [];
      draggingVertexIdx = null;
      clearVertexEditLayer();
    }
    selectedColonyId = col.id;
    selectedPartIndex = partIdx || 0;
    groupSelectionIds = [];
    hideTooltip();

    if (editorGroupPane) editorGroupPane.style.display = "none";
    if (editorVertexPane) editorVertexPane.style.display = "none";
    if (editorSinglePane) editorSinglePane.style.display = "block";

    const partsCount = (col.polygons && col.polygons.length) || 1;
    const kindLabel = col.discarded
      ? `Polígono #${col.id} (Não é Coral)`
      : col.is_grouped || partsCount > 1
      ? `Grupo #${col.id} — ${col.genus}`
      : `Colônia #${col.id} — ${col.genus}`;

    if (editorColorDot) {
      editorColorDot.style.backgroundColor = col.discarded ? "#94a3b8" : col.color;
    }
    if (editorColonyTitle) editorColonyTitle.textContent = kindLabel;

    if (editorColonyMetrics) {
      const partsInfo = partsCount > 1 ? ` &bull; <strong>${partsCount}</strong> polígonos` : "";
      editorColonyMetrics.innerHTML = `Área: <strong>${col.area_cm2} cm²</strong> (${col.area_pct}%)${partsInfo} &bull; Conf.: <strong>${(col.confidence * 100).toFixed(1)}%</strong>`;
    }

    if (editorColonySource) {
      const editedSuffix =
        col.is_geometry_edited && !col.is_manual_drawn ? " &bull; ✒️ Borda Editada" : "";
      if (col.discarded) {
        editorColonySource.textContent =
          col.discard_reason === "fewshot_non_coral"
            ? `🚫 Filtrado automaticamente pelo Few-Shot Não-Coral (sim: ${(col.non_coral_sim || 0).toFixed(2)})`
            : "🚫 Descartado manualmente como Não é Coral";
      } else if (col.is_manual_drawn) {
        editorColonySource.innerHTML =
          col.has_embedding === false
            ? "✍️ Demarcado Manualmente (Offline)"
            : "✍️ Demarcado Manualmente + Vetor BioCLIP 2.5";
      } else if (col.is_grouped) {
        editorColonySource.innerHTML = `🔗 Colônia agrupada (${partsCount} polígonos unidos)${editedSuffix}`;
      } else if (col.manual_locked) {
        editorColonySource.innerHTML = `✏️ Confirmado manualmente por você${editedSuffix}`;
      } else if (col.used_fewshot) {
        editorColonySource.innerHTML = `🧠 BioCLIP 2.5 + Assinatura Few-Shot (sim: ${(col.best_prototype_sim || 0).toFixed(2)})${editedSuffix}`;
      } else {
        editorColonySource.innerHTML = `🤖 BioCLIP 2.5 ReefNet Zero-Shot (${col.views_count || col.sample_points_count} vistas)${editedSuffix}`;
      }
    }

    if (btnEditorTeach) {
      const missingVec = col.has_embedding === false;
      btnEditorTeach.disabled = missingVec;
      btnEditorTeach.title = missingVec
        ? "Polígono manual criado com Colab offline (sem vetor BioCLIP 2.5). Conecte o Colab e use '✒️ Editar Borda' -> 'Salvar Nova Borda' p/ extrair o vetor."
        : "Corrige este polígono, salva a assinatura de 1.024 números do BioCLIP 2.5 e atualiza polígonos similares!";
    }

    if (editorGenusSelect) {
      editorGenusSelect.value = col.discarded ? nonCoralLabel : col.genus;
    }

    // Build Top Coral Candidate Chips + 1-Click "Não é Coral" Chip
    if (editorAltChips) {
      editorAltChips.innerHTML = "";
      const cands = [{ genus: col.genus, confidence: col.confidence, color: col.color }].concat(
        col.alternatives || []
      );
      cands.slice(0, 3).forEach((cand) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "candidate-chip";
        const cColor = cand.color || classColors[cand.genus] || "#38bdf8";
        btn.innerHTML = `<span class="tooltip-color-dot" style="background-color:${cColor};width:8px;height:8px;"></span>${cand.genus} (${(cand.confidence * 100).toFixed(0)}%)`;
        btn.addEventListener("click", () => {
          if (editorGenusSelect) editorGenusSelect.value = cand.genus;
        });
        editorAltChips.appendChild(btn);
      });

      const ncBtn = document.createElement("button");
      ncBtn.type = "button";
      ncBtn.className = "candidate-chip non-coral-chip";
      ncBtn.textContent = "🚫 Não é Coral";
      ncBtn.title = "Selecionar 'Não é Coral' para corrigir ou ensinar o BioCLIP a ignorar falsos positivos similares";
      ncBtn.addEventListener("click", () => {
        if (editorGenusSelect) editorGenusSelect.value = nonCoralLabel;
      });
      editorAltChips.appendChild(ncBtn);
    }

    if (editorActiveActions && editorDiscardedActions) {
      editorActiveActions.style.display = col.discarded ? "none" : "flex";
      editorDiscardedActions.style.display = col.discarded ? "block" : "none";
    }

    renderSubpartsBox(col);

    if (editorFeedbackMsg) {
      if (feedbackText) {
        editorFeedbackMsg.textContent = feedbackText;
        editorFeedbackMsg.style.display = "block";
      } else {
        editorFeedbackMsg.style.display = "none";
      }
    }

    syncPolygonSelectionHighlights();
    colonyEditorCard.style.display = "block";
  }

  function handlePolygonClick(col, partIdx, evt) {
    if (isPickingQuadrat || isDrawingManualPolygon || isEditingVertices) return;
    const isModifier = evt && (evt.shiftKey || evt.ctrlKey || evt.metaKey);

    if ((isModifier || isMultiSelectMode) && !col.discarded) {
      pendingGroupReturnIds = null;
      if (groupSelectionIds.length === 0 && selectedColonyId !== null) {
        const prevCol =
          currentResult && currentResult.colonies.find((c) => c.id === selectedColonyId);
        if (prevCol && !prevCol.discarded) {
          groupSelectionIds = [selectedColonyId];
        }
      }

      if (groupSelectionIds.includes(col.id)) {
        groupSelectionIds = groupSelectionIds.filter((id) => id !== col.id);
      } else {
        groupSelectionIds.push(col.id);
      }
      openGroupInspector();
      return;
    }

    pendingGroupReturnIds = null;
    isMultiSelectMode = false;
    updateMultiselectBannerUi();
    openColonyEditor(col, partIdx);
  }

  if (btnCloseEditor) {
    btnCloseEditor.addEventListener("click", closeColonyEditor);
  }

  if (btnStartGroupSelect) {
    btnStartGroupSelect.addEventListener("click", () => {
      if (!currentResult || selectedColonyId === null) return;
      groupSelectionIds = [selectedColonyId];
      isMultiSelectMode = true;
      openGroupInspector();
    });
  }

  if (btnToggleAddMore) {
    btnToggleAddMore.addEventListener("click", () => {
      isMultiSelectMode = !isMultiSelectMode;
      updateMultiselectBannerUi();
    });
  }

  if (btnDoneMultiselect) {
    btnDoneMultiselect.addEventListener("click", () => {
      isMultiSelectMode = false;
      updateMultiselectBannerUi();
      if (groupSelectionIds.length >= 2) {
        openGroupInspector();
      }
    });
  }

  if (btnCancelGroupSelect) {
    btnCancelGroupSelect.addEventListener("click", closeColonyEditor);
  }

  // Apply updated result from instant local edit / teach / group / part split without resetting Pan & Zoom!
  function applyInstantSessionUpdate(
    updatedData,
    fewshotData,
    keepSelectedId = null,
    feedbackText = null
  ) {
    const prevBg = showingEnhancedBg;
    currentResult = updatedData;
    if (fewshotData) renderFewshotSummary(fewshotData);
    renderResults(currentResult, prevBg, true); // preserveZoom = true

    // If user came from a multi-select grouping warning to unify a divergent polygon's genus, return directly to grouping!
    if (pendingGroupReturnIds && pendingGroupReturnIds.length >= 2) {
      const validIds = pendingGroupReturnIds.filter((cid) => {
        const c = currentResult.colonies.find((x) => x.id === cid);
        return Boolean(c && !c.discarded);
      });
      pendingGroupReturnIds = null;
      if (validIds.length >= 2) {
        groupSelectionIds = validIds;
        openGroupInspector(feedbackText);
        return;
      }
    }

    if (keepSelectedId !== null) {
      const updatedCol = currentResult.colonies.find((c) => c.id === keepSelectedId);
      if (updatedCol && (!updatedCol.discarded || showDiscardedPolygons)) {
        openColonyEditor(updatedCol, selectedPartIndex, feedbackText);
      } else {
        closeColonyEditor();
      }
    } else {
      closeColonyEditor();
    }
  }

  // Button 1: Correct + Teach BioCLIP 2.5 Few-Shot Signature (Coral Genus OR Non-Coral)
  if (btnEditorTeach) {
    btnEditorTeach.addEventListener("click", async () => {
      if (!currentResult || selectedColonyId === null) return;
      const newGenus = editorGenusSelect.value;
      const origText = btnEditorTeach.textContent;
      btnEditorTeach.disabled = true;
      btnEditorTeach.textContent = "⏳ Salvando assinatura e filtrando...";

      try {
        const resp = await fetch("/api/colony/teach", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: currentResult.image_filename,
            colony_id: selectedColonyId,
            genus: newGenus
          })
        });
        const json = await resp.json();
        if (!json.success) throw new Error(json.error || "Falha ao ensinar assinatura.");

        if (json.taught_non_coral) {
          const autoDisc = json.auto_discarded_similar || 0;
          applyInstantSessionUpdate(json.data, json.fewshot, null, null);
          if (autoDisc > 0) {
            // Brief non-blocking feedback in toolbar badge or alert only if needed
            colonyCountBadge.textContent = `${json.data.total_colonies} colônias (+${autoDisc} não-coral filtrados!)`;
          }
        } else {
          const simCount = json.changed_similar_colonies || 0;
          const msg =
            simCount > 0
              ? `✅ Assinatura salva! +${simCount} colônia(s) similar(es) atualizada(s) automaticamente.`
              : `✅ Assinatura de ${newGenus} salva na memória Few-Shot!`;
          applyInstantSessionUpdate(json.data, json.fewshot, selectedColonyId, msg);
        }
      } catch (err) {
        alert(`Erro: ${err.message}`);
      } finally {
        btnEditorTeach.disabled = false;
        btnEditorTeach.textContent = origText;
      }
    });
  }

  // Button 2: Edit ONLY this polygon's label (Coral Genus OR Non-Coral, no Few-Shot learning)
  if (btnEditorSaveOnly) {
    btnEditorSaveOnly.addEventListener("click", async () => {
      if (!currentResult || selectedColonyId === null) return;
      const newGenus = editorGenusSelect.value;
      btnEditorSaveOnly.disabled = true;

      try {
        const resp = await fetch("/api/colony/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: currentResult.image_filename,
            colony_id: selectedColonyId,
            action: "set_genus",
            genus: newGenus
          })
        });
        const json = await resp.json();
        if (!json.success) throw new Error(json.error || "Falha ao atualizar rótulo.");

        const keepId = newGenus === nonCoralLabel ? null : selectedColonyId;
        applyInstantSessionUpdate(
          json.data,
          json.fewshot,
          keepId,
          `✏️ Classificação atualizada para ${newGenus === nonCoralLabel ? "Não é Coral" : newGenus}.`
        );
      } catch (err) {
        alert(`Erro: ${err.message}`);
      } finally {
        btnEditorSaveOnly.disabled = false;
      }
    });
  }

  // Button 3: Quick 1-Click Discard as Non-Coral (manual only)
  if (btnEditorDelete) {
    btnEditorDelete.addEventListener("click", async () => {
      if (!currentResult || selectedColonyId === null) return;
      btnEditorDelete.disabled = true;

      try {
        const resp = await fetch("/api/colony/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: currentResult.image_filename,
            colony_id: selectedColonyId,
            action: "delete"
          })
        });
        const json = await resp.json();
        if (!json.success) throw new Error(json.error || "Falha ao descartar polígono.");

        applyInstantSessionUpdate(json.data, json.fewshot, null, null);
      } catch (err) {
        alert(`Erro: ${err.message}`);
      } finally {
        btnEditorDelete.disabled = false;
      }
    });
  }

  // Button 4: Restore a discarded Non-Coral polygon back to active Coral
  if (btnEditorRestore) {
    btnEditorRestore.addEventListener("click", async () => {
      if (!currentResult || selectedColonyId === null) return;
      const chosenGenus =
        editorGenusSelect && editorGenusSelect.value !== nonCoralLabel
          ? editorGenusSelect.value
          : null;
      btnEditorRestore.disabled = true;

      try {
        const resp = await fetch("/api/colony/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: currentResult.image_filename,
            colony_id: selectedColonyId,
            action: "restore",
            genus: chosenGenus
          })
        });
        const json = await resp.json();
        if (!json.success) throw new Error(json.error || "Falha ao restaurar polígono.");

        applyInstantSessionUpdate(
          json.data,
          json.fewshot,
          selectedColonyId,
          "♻️ Polígono restaurado como coral ativo!"
        );
      } catch (err) {
        alert(`Erro: ${err.message}`);
      } finally {
        btnEditorRestore.disabled = false;
      }
    });
  }

  // Button 5: Confirm Grouping of 2+ Same-Genus Polygons into 1 Colony
  if (btnConfirmGroup) {
    btnConfirmGroup.addEventListener("click", async () => {
      if (!currentResult || groupSelectionIds.length < 2) return;
      btnConfirmGroup.disabled = true;
      const origText = btnConfirmGroup.textContent;
      btnConfirmGroup.textContent = "⏳ Agrupando polígonos...";

      try {
        const resp = await fetch("/api/colony/group", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_name: currentResult.image_filename,
            colony_ids: groupSelectionIds
          })
        });
        const json = await resp.json();
        if (!json.success) throw new Error(json.error || "Falha ao agrupar polígonos.");

        isMultiSelectMode = false;
        groupSelectionIds = [];
        updateMultiselectBannerUi();
        const mergedId = json.group_info ? json.group_info.merged_into_id : null;
        selectedPartIndex = 0;
        applyInstantSessionUpdate(
          json.data,
          json.fewshot,
          mergedId,
          `🔗 Grupo #${mergedId} criado (${json.group_info.parts_count} polígonos = ${json.group_info.area_cm2} cm²)!`
        );
      } catch (err) {
        alert(err.message);
      } finally {
        btnConfirmGroup.disabled = false;
        btnConfirmGroup.textContent = origText;
      }
    });
  }

  // Sub-polygon Part Modification Helper (split / discard_part / explode)
  async function executePartAction(actionName) {
    if (!currentResult || selectedColonyId === null) return;
    try {
      const resp = await fetch("/api/colony/part", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_name: currentResult.image_filename,
          colony_id: selectedColonyId,
          part_index: selectedPartIndex,
          action: actionName
        })
      });
      const json = await resp.json();
      if (!json.success) throw new Error(json.error || "Falha ao editar parte do grupo.");

      selectedPartIndex = 0;
      const msgMap = {
        split: `✂️ Parte separada como nova Colônia #${json.part_info.new_colony_id}!`,
        discard_part: "🗑️ Sub-polígono removido do grupo e descartado.",
        explode: "💥 Grupo desfeito em colônias individuais."
      };
      const keepId = json.part_info.remaining_parts > 0 ? selectedColonyId : null;
      applyInstantSessionUpdate(json.data, json.fewshot, keepId, msgMap[actionName]);
    } catch (err) {
      alert(`Erro: ${err.message}`);
    }
  }

  if (btnPartSplit) {
    btnPartSplit.addEventListener("click", () => executePartAction("split"));
  }
  if (btnPartDiscard) {
    btnPartDiscard.addEventListener("click", () => executePartAction("discard_part"));
  }
  if (btnGroupExplode) {
    btnGroupExplode.addEventListener("click", () => executePartAction("explode"));
  }

  // =========================================================================
  // 6B. POST-PROCESSING MANUAL POLYGON DEMARCATION & VERTEX EDITING
  // =========================================================================
  function updateManualDrawUi() {
    const count = manualDrawPoints.length;
    if (manualDrawMetrics) {
      const hint =
        count >= 3
          ? "Pronto p/ fechar (clique no <strong>1º ponto verde</strong>, <code>Enter</code> ou Salvar)"
          : "Clique p/ marcar pontos ou <strong>Shift+Arraste</strong> p/ laço contínuo";
      manualDrawMetrics.innerHTML = `Vértices: <strong>${count}</strong> &bull; ${hint}`;
    }
    if (btnSaveManualDraw && !isSavingManualPolygon) {
      btnSaveManualDraw.disabled = count < 3;
    }
    if (btnUndoManualVertex) {
      btnUndoManualVertex.disabled = isSavingManualPolygon || count === 0;
    }
    if (manualDrawBioclipNote) {
      const hasColab = Boolean(colabUrlInput && colabUrlInput.value.trim());
      const isAuto =
        manualDrawGenusSelect && manualDrawGenusSelect.value === "__AUTO_BIOCLIP__";
      if (hasColab) {
        manualDrawBioclipNote.innerHTML =
          "🧬 Colab configurado: o vetor <strong>BioCLIP 2.5 (1024-D)</strong> será extraído automaticamente (~0.3s) para permitir Few-Shot!";
      } else if (isAuto) {
        manualDrawBioclipNote.innerHTML =
          "⚠️ Sem URL do Colab: conecte o Colab no Passo 1 p/ auto-classificar ou escolha um dos <strong>11 gêneros</strong> acima para salvar offline.";
      } else {
        manualDrawBioclipNote.innerHTML =
          "ℹ️ Colab offline: a nova colônia será salva localmente com o gênero escolhido e área exata em cm².";
      }
    }
  }

  function renderManualDrawOverlay() {
    if (!stageSvg) return;
    let layer = document.getElementById("manual-draw-layer");
    if (!isDrawingManualPolygon) {
      if (layer) layer.remove();
      return;
    }
    if (!layer) {
      layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
      layer.setAttribute("id", "manual-draw-layer");
      stageSvg.appendChild(layer);
    } else if (stageSvg.lastElementChild !== layer) {
      stageSvg.appendChild(layer);
    }
    layer.innerHTML = "";

    const count = manualDrawPoints.length;
    if (count === 0) return;

    const selVal = manualDrawGenusSelect ? manualDrawGenusSelect.value : "__AUTO_BIOCLIP__";
    const drawColor =
      selVal !== "__AUTO_BIOCLIP__" ? classColors[selVal] || "#10b981" : "#10b981";
    const vRad = Math.max(
      4.5,
      Math.min(24, (currentImageDimensions.width * 0.0044) / Math.pow(zoomLevel, 0.72))
    );
    const firstRad = vRad * 1.48;
    const strokeW = Math.max(
      2.2,
      (currentImageDimensions.width * 0.0014) / Math.pow(zoomLevel, 0.55)
    );

    const ptsStr = manualDrawPoints.map((p) => `${p[0]},${p[1]}`).join(" ");

    if (count >= 3) {
      const polyEl = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
      polyEl.setAttribute("points", ptsStr);
      polyEl.setAttribute("fill", drawColor);
      polyEl.setAttribute("stroke", drawColor);
      polyEl.setAttribute("stroke-width", strokeW);
      polyEl.setAttribute("class", "manual-draw-poly");
      layer.appendChild(polyEl);
    }

    if (count >= 2) {
      const lineEl = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      lineEl.setAttribute("points", ptsStr);
      lineEl.setAttribute("stroke", drawColor);
      lineEl.setAttribute("stroke-width", strokeW * 1.15);
      lineEl.setAttribute("class", "manual-draw-polyline");
      layer.appendChild(lineEl);
    }

    if (manualHoverPoint && !isFreehandLassoActive) {
      const lastPt = manualDrawPoints[count - 1];
      const rb = document.createElementNS("http://www.w3.org/2000/svg", "line");
      rb.setAttribute("x1", lastPt[0]);
      rb.setAttribute("y1", lastPt[1]);
      rb.setAttribute("x2", manualHoverPoint[0]);
      rb.setAttribute("y2", manualHoverPoint[1]);
      rb.setAttribute("stroke-width", strokeW * 0.95);
      rb.setAttribute("class", "manual-draw-rubberband");
      layer.appendChild(rb);
    }

    const stride = count > 80 ? Math.ceil(count / 65) : 1;
    for (let i = 1; i < count; i += stride) {
      const pt = manualDrawPoints[i];
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", pt[0]);
      dot.setAttribute("cy", pt[1]);
      dot.setAttribute("r", vRad * 0.85);
      dot.setAttribute("stroke-width", Math.max(1.4, vRad * 0.25));
      dot.setAttribute("class", "manual-draw-vertex");
      layer.appendChild(dot);
    }

    // First vertex (green snap-to-close target)
    const p0 = manualDrawPoints[0];
    const firstDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    firstDot.setAttribute("cx", p0[0]);
    firstDot.setAttribute("cy", p0[1]);
    firstDot.setAttribute("r", firstRad);
    firstDot.setAttribute("stroke-width", Math.max(2, firstRad * 0.24));
    firstDot.setAttribute("class", "manual-draw-first-vertex");
    firstDot.addEventListener("click", (e) => {
      e.stopPropagation();
      if (manualDrawPoints.length >= 3) {
        saveManualPolygon();
      }
    });
    layer.appendChild(firstDot);
  }

  function startManualDrawMode() {
    if (
      !currentResult ||
      !imageSelect ||
      currentResult.image_filename !== imageSelect.value
    ) {
      alert("Execute o pipeline nesta foto antes de adicionar polígonos de pós-processamento.");
      return;
    }
    if (activeViewMode !== "interactive") {
      btnModeInteractive.click();
    }
    if (isPickingQuadrat) {
      isPickingQuadrat = false;
      pickingCorners = [];
      updateQuadratUiState();
      redrawSvgScene();
    }
    closeColonyEditor();
    hideTooltip();

    isDrawingManualPolygon = true;
    manualDrawPoints = [];
    manualHoverPoint = null;
    isFreehandLassoActive = false;
    isSavingManualPolygon = false;

    if (stageSvg) stageSvg.classList.add("drawing-polygon");
    if (manualDrawCard) manualDrawCard.style.display = "block";
    syncManualDrawColorDot();
    updateManualDrawUi();
    updateVisibilityControlsUi();
    renderManualDrawOverlay();
  }

  function exitManualDrawMode() {
    isDrawingManualPolygon = false;
    manualDrawPoints = [];
    manualHoverPoint = null;
    isFreehandLassoActive = false;
    isSavingManualPolygon = false;
    if (stageSvg) stageSvg.classList.remove("drawing-polygon");
    if (manualDrawCard) manualDrawCard.style.display = "none";
    if (btnSaveManualDraw) {
      btnSaveManualDraw.textContent = "💾 Fechar & Salvar Colônia";
      btnSaveManualDraw.disabled = true;
    }
    clearManualDrawLayer();
    updateVisibilityControlsUi();
  }

  function undoLastManualVertex() {
    if (!isDrawingManualPolygon || manualDrawPoints.length === 0 || isSavingManualPolygon) return;
    manualDrawPoints.pop();
    updateManualDrawUi();
    renderManualDrawOverlay();
  }

  async function saveManualPolygon() {
    if (!currentResult || !isDrawingManualPolygon || isSavingManualPolygon) return;
    if (manualDrawPoints.length < 3) {
      alert("Marque pelo menos 3 vértices para fechar o polígono da colônia.");
      return;
    }

    const chosenGenus = manualDrawGenusSelect
      ? manualDrawGenusSelect.value
      : "__AUTO_BIOCLIP__";
    const colabUrl = colabUrlInput ? colabUrlInput.value.trim() : "";

    isSavingManualPolygon = true;
    if (btnSaveManualDraw) {
      btnSaveManualDraw.disabled = true;
      btnSaveManualDraw.textContent = colabUrl
        ? "⏳ Extraindo BioCLIP 2.5 & salvando..."
        : "⏳ Calculando cm² & salvando...";
    }
    if (btnUndoManualVertex) btnUndoManualVertex.disabled = true;

    try {
      const resp = await fetch("/api/colony/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_name: currentResult.image_filename,
          polygon: manualDrawPoints,
          genus: chosenGenus,
          colab_url: colabUrl
        })
      });
      const json = await resp.json();
      if (!json.success) {
        throw new Error(json.error || "Falha ao adicionar polígono manual.");
      }

      const info = json.add_info || {};
      exitManualDrawMode();
      if (!polygonsVisible) {
        polygonsVisible = true;
        updateVisibilityControlsUi();
      }
      const vecNote = info.extracted_bioclip
        ? " + vetor BioCLIP 2.5 (1024-D) extraído na GPU!"
        : "";
      applyInstantSessionUpdate(
        json.data,
        json.fewshot,
        info.new_colony_id || null,
        `✅ Nova Colônia #${info.new_colony_id} (${info.genus}, ${info.area_cm2} cm²) criada${vecNote}`
      );
    } catch (err) {
      alert(err.message);
      isSavingManualPolygon = false;
      if (btnSaveManualDraw) {
        btnSaveManualDraw.textContent = "💾 Fechar & Salvar Colônia";
      }
      updateManualDrawUi();
    }
  }

  if (btnDrawPolygon) {
    btnDrawPolygon.addEventListener("click", () => {
      if (isDrawingManualPolygon) {
        exitManualDrawMode();
      } else {
        startManualDrawMode();
      }
    });
  }
  if (btnCloseManualDraw) {
    btnCloseManualDraw.addEventListener("click", exitManualDrawMode);
  }
  if (btnCancelManualDraw) {
    btnCancelManualDraw.addEventListener("click", exitManualDrawMode);
  }
  if (btnUndoManualVertex) {
    btnUndoManualVertex.addEventListener("click", undoLastManualVertex);
  }
  if (btnSaveManualDraw) {
    btnSaveManualDraw.addEventListener("click", saveManualPolygon);
  }
  if (manualDrawGenusSelect) {
    manualDrawGenusSelect.addEventListener("change", updateManualDrawUi);
  }

  // --- Existing Polygon Vertex Editing ---
  function pushVertexUndoSnapshot() {
    vertexUndoStack.push(editingVertices.map((p) => [p[0], p[1]]));
    if (vertexUndoStack.length > 40) {
      vertexUndoStack.shift();
    }
  }

  function updateVertexEditUi() {
    if (vertexEditMetrics) {
      const undoNote =
        vertexUndoStack.length > 0
          ? ` &bull; <strong>${vertexUndoStack.length}</strong> edição(ões)`
          : "";
      vertexEditMetrics.innerHTML = `Vértices na borda: <strong>${editingVertices.length}</strong>${undoNote}`;
    }
    if (btnUndoVertexEdit) {
      btnUndoVertexEdit.disabled = isSavingVertexEdit || vertexUndoStack.length === 0;
    }
    if (btnSaveVertexEdit && !isSavingVertexEdit) {
      btnSaveVertexEdit.disabled = editingVertices.length < 3;
    }
  }

  function renderVertexEditOverlay() {
    if (!stageSvg) return;
    let layer = document.getElementById("vertex-edit-layer");
    if (!isEditingVertices || editingVertices.length < 3 || !currentResult) {
      if (layer) layer.remove();
      return;
    }
    if (!layer) {
      layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
      layer.setAttribute("id", "vertex-edit-layer");
      stageSvg.appendChild(layer);
    } else if (stageSvg.lastElementChild !== layer) {
      stageSvg.appendChild(layer);
    }
    layer.innerHTML = "";

    const col = currentResult.colonies.find((c) => c.id === selectedColonyId);
    const polyColor = (col && col.color) || "#38bdf8";

    const vRadius = Math.max(
      4.5,
      Math.min(24, (currentImageDimensions.width * 0.0043) / Math.pow(zoomLevel, 0.72))
    );
    const midRadius = vRadius * 0.68;
    const handleStrokeW = Math.max(1.4, vRadius * 0.26);
    const polyStrokeW = Math.max(
      2.2,
      (currentImageDimensions.width * 0.0014) / Math.pow(zoomLevel, 0.55)
    );

    const ptsStr = editingVertices.map((p) => `${p[0]},${p[1]}`).join(" ");
    const polyEl = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    polyEl.setAttribute("points", ptsStr);
    polyEl.setAttribute("fill", polyColor);
    polyEl.setAttribute("stroke", "#fbbf24");
    polyEl.setAttribute("stroke-width", polyStrokeW);
    polyEl.setAttribute("class", "vertex-edit-poly");
    layer.appendChild(polyEl);

    const n = editingVertices.length;

    // 1. Edge midpoint (+) handles for inserting new vertices
    for (let i = 0; i < n; i++) {
      const p1 = editingVertices[i];
      const p2 = editingVertices[(i + 1) % n];
      const mx = Math.round((p1[0] + p2[0]) / 2);
      const my = Math.round((p1[1] + p2[1]) / 2);

      const midDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      midDot.setAttribute("cx", mx);
      midDot.setAttribute("cy", my);
      midDot.setAttribute("r", midRadius);
      midDot.setAttribute("stroke-width", handleStrokeW * 0.85);
      midDot.setAttribute("class", "vertex-midpoint-handle");
      midDot.addEventListener("mousedown", (e) => {
        if (e.button !== 0 || isSavingVertexEdit) return;
        e.stopPropagation();
        e.preventDefault();
        pushVertexUndoSnapshot();
        editingVertices.splice(i + 1, 0, [mx, my]);
        draggingVertexIdx = i + 1;
        updateVertexEditUi();
        renderVertexEditOverlay();
      });
      layer.appendChild(midDot);
    }

    // 2. Main draggable/deletable vertex handles
    for (let i = 0; i < n; i++) {
      const pt = editingVertices[i];
      const vDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      vDot.setAttribute("cx", pt[0]);
      vDot.setAttribute("cy", pt[1]);
      vDot.setAttribute("r", vRadius);
      vDot.setAttribute("stroke-width", handleStrokeW);
      vDot.setAttribute("class", "vertex-handle");

      vDot.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        e.stopPropagation();
      });

      vDot.addEventListener("mousedown", (e) => {
        if (isSavingVertexEdit) return;
        e.stopPropagation();
        // Right-click or Alt+Click deletes vertex (min 3 vertices)
        if (e.button === 2 || (e.button === 0 && e.altKey)) {
          e.preventDefault();
          if (editingVertices.length <= 3) {
            if (editorFeedbackMsg) {
              editorFeedbackMsg.textContent = "⚠️ Um polígono precisa ter no mínimo 3 vértices.";
              editorFeedbackMsg.style.display = "block";
            }
            return;
          }
          pushVertexUndoSnapshot();
          editingVertices.splice(i, 1);
          updateVertexEditUi();
          renderVertexEditOverlay();
          return;
        }
        if (e.button === 0) {
          e.preventDefault();
          pushVertexUndoSnapshot();
          draggingVertexIdx = i;
          updateVertexEditUi();
        }
      });

      layer.appendChild(vDot);
    }
  }

  function startVertexEditMode() {
    if (!currentResult || selectedColonyId === null) return;
    const col = currentResult.colonies.find((c) => c.id === selectedColonyId);
    if (!col || col.discarded) return;

    const polys =
      col.polygons && col.polygons.length > 0
        ? col.polygons
        : col.polygon && col.polygon.length >= 3
        ? [col.polygon]
        : [];
    if (polys.length === 0) return;

    if (selectedPartIndex < 0 || selectedPartIndex >= polys.length) {
      selectedPartIndex = 0;
    }

    if (isDrawingManualPolygon) exitManualDrawMode();
    hideTooltip();

    editingVertices = polys[selectedPartIndex].map((p) => [Math.round(p[0]), Math.round(p[1])]);
    vertexUndoStack = [];
    draggingVertexIdx = null;
    isSavingVertexEdit = false;
    isEditingVertices = true;

    if (editorSinglePane) editorSinglePane.style.display = "none";
    if (editorGroupPane) editorGroupPane.style.display = "none";
    if (editorVertexPane) editorVertexPane.style.display = "block";
    if (editorFeedbackMsg) editorFeedbackMsg.style.display = "none";

    if (editorColonyTitle) {
      editorColonyTitle.textContent =
        polys.length > 1
          ? `✒️ Borda: Grupo #${col.id} (Parte #${selectedPartIndex + 1})`
          : `✒️ Borda: Colônia #${col.id} (${col.genus})`;
    }

    updateVertexEditUi();
    syncPolygonSelectionHighlights();
    renderVertexEditOverlay();
  }

  function undoVertexEditStep() {
    if (!isEditingVertices || vertexUndoStack.length === 0 || isSavingVertexEdit) return;
    editingVertices = vertexUndoStack.pop();
    draggingVertexIdx = null;
    updateVertexEditUi();
    renderVertexEditOverlay();
  }

  function cancelVertexEditMode() {
    const prevId = selectedColonyId;
    const prevPart = selectedPartIndex;
    isEditingVertices = false;
    editingVertices = [];
    vertexUndoStack = [];
    draggingVertexIdx = null;
    isSavingVertexEdit = false;
    clearVertexEditLayer();

    const col = currentResult && currentResult.colonies.find((c) => c.id === prevId);
    if (col) {
      openColonyEditor(col, prevPart);
    } else {
      closeColonyEditor();
    }
  }

  async function saveVertexEdit() {
    if (!currentResult || !isEditingVertices || selectedColonyId === null || isSavingVertexEdit) {
      return;
    }
    if (editingVertices.length < 3) {
      alert("O polígono precisa ter pelo menos 3 vértices.");
      return;
    }

    const colabUrl = colabUrlInput ? colabUrlInput.value.trim() : "";
    const refreshBioclip = chkRefreshBioclip ? Boolean(chkRefreshBioclip.checked) : true;
    const targetId = selectedColonyId;
    const targetPart = selectedPartIndex;

    isSavingVertexEdit = true;
    if (btnSaveVertexEdit) {
      btnSaveVertexEdit.disabled = true;
      btnSaveVertexEdit.textContent =
        refreshBioclip && colabUrl
          ? "⏳ Atualizando borda & BioCLIP..."
          : "⏳ Recalculando cm² & salvando...";
    }
    if (btnUndoVertexEdit) btnUndoVertexEdit.disabled = true;

    try {
      const resp = await fetch("/api/colony/edit-polygon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_name: currentResult.image_filename,
          colony_id: targetId,
          part_index: targetPart,
          polygon: editingVertices,
          colab_url: colabUrl,
          refresh_bioclip: refreshBioclip
        })
      });
      const json = await resp.json();
      if (!json.success) {
        throw new Error(json.error || "Falha ao salvar nova borda do polígono.");
      }

      const info = json.edit_info || {};
      isEditingVertices = false;
      editingVertices = [];
      vertexUndoStack = [];
      draggingVertexIdx = null;
      isSavingVertexEdit = false;
      if (btnSaveVertexEdit) {
        btnSaveVertexEdit.textContent = "💾 Salvar Nova Borda";
        btnSaveVertexEdit.disabled = false;
      }
      clearVertexEditLayer();

      selectedPartIndex = Math.min(targetPart, Math.max(0, (info.parts_count || 1) - 1));
      const vecMsg = info.refreshed_bioclip ? " + vetor BioCLIP 2.5 atualizado!" : "!";
      applyInstantSessionUpdate(
        json.data,
        json.fewshot,
        targetId,
        `✒️ Borda atualizada (${info.area_cm2} cm² / ${info.area_pct}%)${vecMsg}`
      );
    } catch (err) {
      alert(err.message);
      isSavingVertexEdit = false;
      if (btnSaveVertexEdit) {
        btnSaveVertexEdit.textContent = "💾 Salvar Nova Borda";
      }
      updateVertexEditUi();
    }
  }

  if (btnStartVertexEdit) {
    btnStartVertexEdit.addEventListener("click", startVertexEditMode);
  }
  if (btnUndoVertexEdit) {
    btnUndoVertexEdit.addEventListener("click", undoVertexEditStep);
  }
  if (btnCancelVertexEdit) {
    btnCancelVertexEdit.addEventListener("click", cancelVertexEditMode);
  }
  if (btnSaveVertexEdit) {
    btnSaveVertexEdit.addEventListener("click", saveVertexEdit);
  }

  // Few-Shot Sidebar Toggle, Reclassify & Clear Handlers
  if (chkFewshotEnabled) {
    chkFewshotEnabled.addEventListener("change", async () => {
      const enabled = chkFewshotEnabled.checked;
      const openImg = currentResult ? currentResult.image_filename : null;
      try {
        const resp = await fetch("/api/fewshot/toggle", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled, image_name: openImg })
        });
        const json = await resp.json();
        if (json.fewshot) renderFewshotSummary(json.fewshot);
        if (json.data) applyInstantSessionUpdate(json.data, json.fewshot, selectedColonyId);
      } catch (err) {
        console.error(err);
      }
    });
  }

  if (btnReclassifyPhoto) {
    btnReclassifyPhoto.addEventListener("click", async () => {
      const openImg = currentResult ? currentResult.image_filename : imageSelect.value;
      if (!openImg) return;
      btnReclassifyPhoto.disabled = true;
      try {
        const resp = await fetch("/api/reclassify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_name: openImg, unlock_manual: false })
        });
        const json = await resp.json();
        if (json.success && json.data) {
          applyInstantSessionUpdate(json.data, json.fewshot, selectedColonyId);
        } else if (json.error) {
          alert(json.error);
        }
      } catch (err) {
        alert(`Erro ao reclassificar: ${err.message}`);
      } finally {
        btnReclassifyPhoto.disabled = false;
      }
    });
  }

  if (btnClearFewshot) {
    btnClearFewshot.addEventListener("click", async () => {
      if (
        !confirm(
          "Deseja limpar todas as assinaturas Few-Shot salvas e voltar ao BioCLIP 2.5 Zero-Shot puro?"
        )
      ) {
        return;
      }
      const openImg = currentResult ? currentResult.image_filename : null;
      try {
        const resp = await fetch("/api/fewshot/clear", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image_name: openImg })
        });
        const json = await resp.json();
        if (json.fewshot) renderFewshotSummary(json.fewshot);
        if (json.data) applyInstantSessionUpdate(json.data, json.fewshot, null);
      } catch (err) {
        alert(`Erro ao limpar memória: ${err.message}`);
      }
    });
  }

  // =========================================================================
  // 7. SVG SCENE RENDERING (POLYGONS, SUB-PARTS, DISCARDED, QUADRAT 4-CORNERS)
  // =========================================================================
  function syncPhotoQuadratStatus(filename) {
    if (!filename) return;
    const hasQuad = Boolean(
      (quadratCornersByImage[filename] && quadratCornersByImage[filename].length === 4) ||
      (currentResult && currentResult.image_filename === filename && (currentResult.has_quadrat_roi || (currentResult.quadrat_corners && currentResult.quadrat_corners.length === 4)))
    );

    // 1. Update in workspaceImages array
    const imgObj = workspaceImages.find((x) => x.filename === filename);
    if (imgObj) {
      imgObj.has_quadrat_roi = hasQuad;
      if (hasQuad && quadratCornersByImage[filename]) {
        imgObj.quadrat_corners = quadratCornersByImage[filename];
      } else if (!hasQuad) {
        imgObj.quadrat_corners = null;
      }
    }

    // 2. Direct DOM update on the photo item badge in checklist
    if (photoChecklistItems) {
      const itemEl = Array.from(photoChecklistItems.querySelectorAll(".photo-check-item")).find(
        (el) => el.dataset.filename === filename
      );
      if (itemEl) {
        const quadBadge = itemEl.querySelector(".pipe-badge-quadrat");
        if (quadBadge) {
          quadBadge.className = `pipe-badge pipe-badge-quadrat ${hasQuad ? "pipe-active" : "pipe-muted"}`;
          quadBadge.title = hasQuad ? "Quadrante 4 cantos calibrado por homografia" : "Foto inteira (sem recorte de PVC)";
          quadBadge.textContent = hasQuad ? "📐 PVC 4C" : "📐 Geral";
        }
      }
    }
  }

  function updateQuadratUiState() {
    const imgName = imageSelect ? imageSelect.value : "";
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

    if (imgName) {
      syncPhotoQuadratStatus(imgName);
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
    const baseAlpha = outlineOnlyMode ? 0.0 : opacitySlider.value / 100.0;
    const multiSet = new Set(groupSelectionIds);

    // 1. Draw Colony Polygons if currentResult matches selected image and polygonsVisible is true
    if (polygonsVisible && currentResult && currentResult.image_filename === imgName) {
      currentResult.colonies.forEach((col) => {
        if (col.discarded && !showDiscardedPolygons) {
          return;
        }

        const polyList =
          col.polygons && col.polygons.length > 0
            ? col.polygons
            : col.polygon && col.polygon.length >= 3
            ? [col.polygon]
            : [];

        const isMulti = multiSet.size >= 2 && multiSet.has(col.id);
        const isSingle = multiSet.size < 2 && selectedColonyId === col.id;
        const fillCol = col.discarded ? "#94a3b8" : col.color;
        const fillAlpha = col.discarded ? (outlineOnlyMode ? 0.0 : 0.14) : baseAlpha;

        polyList.forEach((polyPts, partIdx) => {
          if (!polyPts || polyPts.length < 3) return;
          const ptsStr = polyPts.map((p) => `${p[0]},${p[1]}`).join(" ");

          const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
          polygon.setAttribute("points", ptsStr);
          polygon.setAttribute("fill", fillCol);
          polygon.setAttribute("fill-opacity", fillAlpha);
          polygon.setAttribute("stroke", fillCol);
          polygon.setAttribute("stroke-width", col.is_grouped || polyList.length > 1 ? "4.8" : "3.8");

          const isBeingEdited =
            isEditingVertices && selectedColonyId === col.id && partIdx === selectedPartIndex;
          const classes = ["colony-polygon"];
          if (col.discarded) classes.push("discarded-polygon");
          if (isMulti) classes.push("group-selected-colony");
          if (isSingle && !isBeingEdited) classes.push("selected-colony");
          if (isSingle && polyList.length >= 2 && partIdx === selectedPartIndex && !isBeingEdited) {
            classes.push("selected-subpart");
          }
          if (isBeingEdited) classes.push("being-vertex-edited");

          polygon.setAttribute("class", classes.join(" "));
          polygon.setAttribute("data-id", col.id);
          polygon.setAttribute("data-part-idx", partIdx);
          polygon.setAttribute("data-total-parts", polyList.length);
          polygon.setAttribute("data-genus", col.genus);
          polygon.setAttribute("data-discarded", col.discarded ? "1" : "0");

          polygon.addEventListener("mouseenter", (e) => {
            if (
              !isPickingQuadrat &&
              !isDrawingManualPolygon &&
              !isEditingVertices &&
              !isPointerDownForPan
            ) {
              showTooltip(e, col, partIdx, polyList.length);
            }
          });
          polygon.addEventListener("mousemove", (e) => {
            if (
              !isPickingQuadrat &&
              !isDrawingManualPolygon &&
              !isEditingVertices &&
              !isPointerDownForPan
            ) {
              moveTooltip(e);
            }
          });
          polygon.addEventListener("mouseleave", () => {
            hideTooltip();
          });
          polygon.addEventListener("click", (e) => {
            if (performance.now() < suppressClickUntil) return;
            if (isPickingQuadrat || isDrawingManualPolygon || isEditingVertices) return;
            e.stopPropagation();
            handlePolygonClick(col, partIdx, e);
          });

          stageSvg.appendChild(polygon);
        });

        // Multi-point interior crosshairs (active colonies only, hidden in outline-only mode for clean corallite view)
        if (!col.discarded && !outlineOnlyMode && col.sample_points && col.sample_points.length > 1) {
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

    // 2. Draw 4-Corner Quadrat Overlay
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

    // 3. Keep Active Manual Drawing or Vertex Editing Overlay on Top (Even if Polygons Are Hidden via 'V')
    if (isDrawingManualPolygon) {
      renderManualDrawOverlay();
    }
    if (isEditingVertices) {
      renderVertexEditOverlay();
    }

    // 4. URL Param Highlight Tooltip
    const urlParams = new URLSearchParams(window.location.search);
    const highlightId = urlParams.get("highlight");
    if (highlightId && currentResult && currentResult.colonies && currentResult.colonies.length > 0) {
      const colId = parseInt(highlightId, 10);
      const col = currentResult.colonies.find((c) => c.id === colId);
      if (col) {
        const polyEl = stageSvg.querySelector(`.colony-polygon[data-id="${colId}"]`);
        if (polyEl) {
          polyEl.classList.add("selected-colony");
          polyEl.style.stroke = "#ffffff";
          polyEl.style.strokeWidth = "8px";
          setTimeout(() => {
            const stageRect = interactiveStage.getBoundingClientRect();
            colonyTooltip.innerHTML = `
              <div class="tooltip-genus">
                <span class="tooltip-color-dot" style="background-color: ${col.color};"></span>
                #${col.id} ${col.genus}
              </div>
              <div>Área Real: <strong>${col.area_cm2} cm²</strong> (${col.area_pct}%)</div>
              <div>🧠 BioCLIP + Few-Shot: <strong>${(col.confidence * 100).toFixed(1)}%</strong></div>
              <div style="font-size: 0.7rem; color: #38bdf8; margin-top: 2px;">Clique p/ editar ou ajustar borda &bull; Shift+Clique p/ agrupar</div>
            `;
            colonyTooltip.style.setProperty("display", "block", "important");
            colonyTooltip.style.left = `${stageRect.width * 0.58}px`;
            colonyTooltip.style.top = `${stageRect.height * 0.26}px`;
          }, 350);
        }
      }
    }
  }

  async function showImageInStage(filename, skipSessionCheck = false) {
    if (!filename) return;
    isPickingQuadrat = false;
    pickingCorners = [];
    draggingCornerIdx = null;
    if (isDrawingManualPolygon) exitManualDrawMode();
    closeColonyEditor();
    resetPanZoom();

    updateActiveThumb(filename);
    updateChecklistActive(filename);

    if (!skipSessionCheck) {
      try {
        const resp = await fetch(`/api/image-session/${encodeURIComponent(filename)}`);
        const sData = await resp.json();

        if (sData.status === "hash_mismatch") {
          if (activePhotoStatusBadge) {
            activePhotoStatusBadge.className = "badge badge-danger";
            activePhotoStatusBadge.textContent = "⚠️ Hash diferente";
          }
          currentResult = null;
          colonyCountBadge.style.display = "none";
          resultsPanel.style.display = "none";
          btnDownloadCsv.style.display = "none";
          opacityControl.style.display = "none";
          if (polygonVisibilityControls) polygonVisibilityControls.style.display = "none";

          alert(
            `⚠️ Imagem Modificada / Hash SHA-256 Alterado:\n\n` +
            `O arquivo '${filename}' foi substituído ou editado no disco após os polígonos terem sido gerados.\n\n` +
            `Os polígonos e classificações anteriores foram desconsiderados por segurança para evitar mapeamento incorreto.\n\n` +
            `Reexecute o CoralSCOP nesta foto para gerar novas anotações alinhadas.`
          );
        } else if (sData.success && sData.data) {
          if (activePhotoStatusBadge) {
            activePhotoStatusBadge.className = "badge badge-success";
            activePhotoStatusBadge.textContent = "✅ Processada";
          }
          currentResult = sData.data;
          if (
            currentResult.quadrat_corners &&
            Array.isArray(currentResult.quadrat_corners) &&
            currentResult.quadrat_corners.length === 4
          ) {
            quadratCornersByImage[filename] = currentResult.quadrat_corners;
          }
          syncPhotoQuadratStatus(filename);
          if (currentResult.fewshot_summary) {
            renderFewshotSummary(currentResult.fewshot_summary);
          }
          renderResults(currentResult, false, false);
        } else {
          if (activePhotoStatusBadge) {
            activePhotoStatusBadge.className = "badge badge-warning";
            activePhotoStatusBadge.textContent = "⏳ Pendente";
          }
          if (!currentResult || currentResult.image_filename !== filename) {
            currentResult = null;
            colonyCountBadge.style.display = "none";
            resultsPanel.style.display = "none";
            btnDownloadCsv.style.display = "none";
            opacityControl.style.display = "none";
            if (polygonVisibilityControls) polygonVisibilityControls.style.display = "none";
          }
        }
      } catch (err) {
        console.warn("Verificação de sessão da foto falhou:", err);
      }
    }

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
        : `/images/${filename}?t=${Date.now()}`;

    viewerPlaceholder.style.display = "none";
    if (zoomHud) zoomHud.style.display = "flex";
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
      updateVisibilityControlsUi();
      redrawSvgScene();
    };
    stageImage.src = targetSrc;
  }

  // SVG Click, Double-Click & Window Drag Handlers (Pan + Manual Draw + Vertex Drag + Quadrat 4-Corner)
  stageSvg.addEventListener("click", (e) => {
    if (performance.now() < suppressClickUntil) return;

    if (isDrawingManualPolygon) {
      if (isSavingManualPolygon) return;
      const pt = clientToSvgCoords(e);
      if (manualDrawPoints.length >= 3) {
        const p0 = manualDrawPoints[0];
        const snapRad = Math.max(
          10,
          (currentImageDimensions.width * 0.011) / Math.pow(zoomLevel, 0.8)
        );
        if (Math.hypot(pt[0] - p0[0], pt[1] - p0[1]) <= snapRad) {
          saveManualPolygon();
          return;
        }
      }
      manualDrawPoints.push(pt);
      updateManualDrawUi();
      renderManualDrawOverlay();
      return;
    }

    if (isEditingVertices) {
      return; // prevent accidental closing while editing vertices
    }

    if (!isPickingQuadrat) {
      if (e.target === stageSvg && !isMultiSelectMode) closeColonyEditor();
      return;
    }
    const imgName = imageSelect.value;
    if (!imgName) return;

    const pt = clientToSvgCoords(e);
    pickingCorners.push(pt);

    if (pickingCorners.length === 4) {
      quadratCornersByImage[imgName] = orderQuadCornersJs(pickingCorners);
      isPickingQuadrat = false;
      pickingCorners = [];
      syncPhotoQuadratStatus(imgName);
    }
    updateQuadratUiState();
    redrawSvgScene();
  });

  stageSvg.addEventListener("dblclick", (e) => {
    if (isDrawingManualPolygon && !isSavingManualPolygon && manualDrawPoints.length >= 3) {
      e.preventDefault();
      e.stopPropagation();
      saveManualPolygon();
    }
  });

  window.addEventListener("mousemove", (e) => {
    if (isEditingVertices && draggingVertexIdx !== null) {
      editingVertices[draggingVertexIdx] = clientToSvgCoords(e);
      renderVertexEditOverlay();
      return;
    }

    if (draggingCornerIdx !== null) {
      const imgName = imageSelect.value;
      if (!imgName || !quadratCornersByImage[imgName]) return;
      const pt = clientToSvgCoords(e);
      quadratCornersByImage[imgName][draggingCornerIdx] = pt;
      redrawSvgScene();
      return;
    }

    if (isDrawingManualPolygon) {
      const pt = clientToSvgCoords(e);
      if (isFreehandLassoActive) {
        const minStep = Math.max(
          6,
          (currentImageDimensions.width * 0.0035) / Math.pow(zoomLevel, 0.75)
        );
        const last = manualDrawPoints[manualDrawPoints.length - 1];
        if (!last || Math.hypot(pt[0] - last[0], pt[1] - last[1]) >= minStep) {
          manualDrawPoints.push(pt);
          updateManualDrawUi();
        }
      }
      manualHoverPoint = pt;
      if (!isPointerDownForPan || !didDragDuringPan) {
        renderManualDrawOverlay();
      }
    }

    if (isPointerDownForPan) {
      const dx = e.clientX - panStartClient.x;
      const dy = e.clientY - panStartClient.y;
      if (!didDragDuringPan && Math.hypot(dx, dy) > 4) {
        didDragDuringPan = true;
        if (interactiveStage) interactiveStage.classList.add("is-panning");
        if (renderedStage) renderedStage.classList.add("is-panning");
        hideTooltip();
      }
      if (didDragDuringPan) {
        panX = panStartOffset.x + dx;
        panY = panStartOffset.y + dy;
        applyPanZoomTransform();
      }
    }
  });

  window.addEventListener("mouseup", () => {
    if (draggingVertexIdx !== null) {
      draggingVertexIdx = null;
      suppressClickUntil = performance.now() + 90;
      renderVertexEditOverlay();
    }

    if (isFreehandLassoActive) {
      isFreehandLassoActive = false;
      suppressClickUntil = performance.now() + 90;
      updateManualDrawUi();
      renderManualDrawOverlay();
    }

    if (draggingCornerIdx !== null) {
      const imgName = imageSelect.value;
      if (imgName && quadratCornersByImage[imgName]) {
        quadratCornersByImage[imgName] = orderQuadCornersJs(quadratCornersByImage[imgName]);
        syncPhotoQuadratStatus(imgName);
      }
      draggingCornerIdx = null;
      redrawSvgScene();
    }

    if (isPointerDownForPan) {
      isPointerDownForPan = false;
      if (interactiveStage) interactiveStage.classList.remove("is-panning");
      if (renderedStage) renderedStage.classList.remove("is-panning");
      if (didDragDuringPan) {
        suppressClickUntil = performance.now() + 90;
        didDragDuringPan = false;
      }
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
      if (isDrawingManualPolygon) exitManualDrawMode();
      closeColonyEditor();
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
        if (currentResult && currentResult.image_filename === imgName) {
          currentResult.has_quadrat_roi = false;
          currentResult.quadrat_corners = null;
        }
        syncPhotoQuadratStatus(imgName);
      }
      isPickingQuadrat = false;
      pickingCorners = [];
      updateQuadratUiState();
      redrawSvgScene();
    });
  }

  // Live Underwater Filter Preview Button
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

  // =========================================================================
  // 8. PROJECT WORKSPACE, SURVEY IMAGES, CHECKLIST & BATCH PIPELINE
  // =========================================================================

  function updateActiveThumb(filename) {
    document.querySelectorAll(".thumb-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.filename === filename || el.title === filename);
    });
  }

  function updateChecklistActive(filename) {
    document.querySelectorAll(".photo-check-item").forEach((el) => {
      const isAct = el.dataset.filename === filename;
      el.classList.toggle("active-photo", isAct);
      if (isAct && el.scrollIntoView) {
        el.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    });
  }

  function getStatusBadgeHtml(status) {
    if (status === "processed") {
      return '<span class="photo-item-badge badge-processed">✅ Processada</span>';
    }
    if (status === "hash_mismatch") {
      return '<span class="photo-item-badge badge-mismatch">⚠️ Alterada</span>';
    }
    return '<span class="photo-item-badge badge-pending">⏳ Pendente</span>';
  }

  function renderPhotoChecklist() {
    if (!photoChecklistItems) return;
    photoChecklistItems.innerHTML = "";
    if (photoTotalCount) photoTotalCount.textContent = workspaceImages.length;
    if (batchSelectedCount) batchSelectedCount.textContent = selectedForBatch.size;

    const activityPhotosCount = document.getElementById("activity-photos-count");
    if (activityPhotosCount) activityPhotosCount.textContent = workspaceImages.length;

    const currentSelectedImg = imageSelect ? imageSelect.value : "";

    workspaceImages.forEach((img) => {
      const item = document.createElement("div");
      item.className = `photo-check-item ${img.filename === currentSelectedImg ? "active-photo" : ""}`;
      item.dataset.filename = img.filename;

      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.checked = selectedForBatch.has(img.filename);
      chk.addEventListener("click", (e) => e.stopPropagation());
      chk.addEventListener("change", (e) => {
        if (e.target.checked) {
          selectedForBatch.add(img.filename);
        } else {
          selectedForBatch.delete(img.filename);
        }
        if (batchSelectedCount) batchSelectedCount.textContent = selectedForBatch.size;
        if (chkSelectAllPhotos) {
          chkSelectAllPhotos.checked =
            workspaceImages.length > 0 && selectedForBatch.size === workspaceImages.length;
        }
      });

      // Mini Thumbnail
      const thumbImg = document.createElement("img");
      thumbImg.className = "photo-item-thumb";
      thumbImg.src = img.url;
      thumbImg.alt = img.filename;
      thumbImg.loading = "lazy";

      // Info Block
      const infoDiv = document.createElement("div");
      infoDiv.className = "photo-item-info";

      const titleRow = document.createElement("div");
      titleRow.className = "photo-item-title-row";

      const nameSpan = document.createElement("span");
      nameSpan.className = "photo-item-name";
      nameSpan.textContent = img.filename;
      nameSpan.title = img.filename;

      const sizeSpan = document.createElement("span");
      sizeSpan.className = "photo-item-size";
      sizeSpan.textContent = `${img.size_mb} MB`;

      titleRow.appendChild(nameSpan);
      titleRow.appendChild(sizeSpan);

      // 3 Pipeline Badges: 🎨 Filter, 📐 Quadrat, 🪸 AI
      const badgesRow = document.createElement("div");
      badgesRow.className = "photo-pipeline-badges";

      // 1. Filter Badge (🎨)
      const hasFilter = img.filter_mode && img.filter_mode !== "none";
      const filterBadge = document.createElement("span");
      filterBadge.className = `pipe-badge ${hasFilter ? "pipe-active" : "pipe-muted"}`;
      filterBadge.title = hasFilter ? `Filtro aplicado: ${img.filter_mode}` : "Foto original (sem filtro)";
      filterBadge.textContent = hasFilter ? "🎨 Realce" : "🎨 Orig.";

      // 2. Quadrat Badge (📐)
      const hasQuad = Boolean(
        img.has_quadrat_roi ||
        (quadratCornersByImage[img.filename] && quadratCornersByImage[img.filename].length === 4)
      );
      const quadBadge = document.createElement("span");
      quadBadge.className = `pipe-badge pipe-badge-quadrat ${hasQuad ? "pipe-active" : "pipe-muted"}`;
      quadBadge.title = hasQuad ? "Quadrante 4 cantos calibrado por homografia" : "Foto inteira (sem recorte de PVC)";
      quadBadge.textContent = hasQuad ? "📐 PVC 4C" : "📐 Geral";

      // 3. AI / Segmentation Badge (🪸)
      const aiBadge = document.createElement("span");
      if (img.status === "processed") {
        aiBadge.className = "pipe-badge pipe-success";
        aiBadge.title = `${img.total_colonies} colônias segmentadas e classificadas`;
        aiBadge.textContent = `🪸 ${img.total_colonies} col.`;
      } else if (img.status === "hash_mismatch") {
        aiBadge.className = "pipe-badge pipe-danger";
        aiBadge.title = "Arquivo de imagem alterado no disco (hash diferente)";
        aiBadge.textContent = "⚠️ Alterada";
      } else {
        aiBadge.className = "pipe-badge pipe-pending";
        aiBadge.title = "Aguardando processamento no CoralSCOP + BioCLIP 2.5";
        aiBadge.textContent = "⏳ Pendente";
      }

      badgesRow.appendChild(filterBadge);
      badgesRow.appendChild(quadBadge);
      badgesRow.appendChild(aiBadge);

      infoDiv.appendChild(titleRow);
      infoDiv.appendChild(badgesRow);

      item.appendChild(chk);
      item.appendChild(thumbImg);
      item.appendChild(infoDiv);

      item.addEventListener("click", () => {
        if (imageSelect) imageSelect.value = img.filename;
        showingEnhancedBg = false;
        showImageInStage(img.filename);
      });

      photoChecklistItems.appendChild(item);
    });
  }

  function renderThumbnailStrip() {
    if (!thumbnailStrip) return;
    thumbnailStrip.innerHTML = "";
    const currentSelectedImg = imageSelect ? imageSelect.value : "";

    workspaceImages.forEach((img) => {
      const thumb = document.createElement("div");
      thumb.className = `thumb-item ${img.filename === currentSelectedImg ? "active" : ""}`;
      thumb.title = `${img.filename} (${img.status === "processed" ? "Processada" : img.status === "hash_mismatch" ? "Hash alterado" : "Pendente"})`;
      thumb.dataset.filename = img.filename;

      const dotClass =
        img.status === "processed"
          ? "dot-processed"
          : img.status === "hash_mismatch"
          ? "dot-mismatch"
          : "dot-pending";

      thumb.innerHTML = `
        <img src="${img.url}?t=${Date.now()}" alt="${img.filename}">
        <span class="thumb-status-dot ${dotClass}"></span>
      `;

      thumb.addEventListener("click", () => {
        if (imageSelect) imageSelect.value = img.filename;
        showingEnhancedBg = false;
        showImageInStage(img.filename);
      });
      thumbnailStrip.appendChild(thumb);
    });
  }

  function renderRecentProjects(recents) {
    if (!recentProjectsList) return;
    recentProjectsList.innerHTML = "";

    if (!recents || recents.length === 0) {
      recentProjectsList.innerHTML =
        '<div class="text-muted" style="text-align: center; padding: 20px;">Nenhum projeto recente salvo. Crie um novo projeto na aba ao lado!</div>';
      return;
    }

    recents.forEach((proj) => {
      const card = document.createElement("div");
      card.className = `recent-proj-card ${proj.is_active ? "is-active" : ""}`;

      const info = document.createElement("div");
      info.className = "recent-proj-info";
      const statusBadge = proj.is_active
        ? '<span class="badge badge-success" style="font-size:0.65rem; padding:1px 5px;">ATIVO</span>'
        : (!proj.exists ? '<span class="badge badge-danger" style="font-size:0.65rem; padding:1px 5px;">PASTA AUSENTE</span>' : '');

      info.innerHTML = `
        <h4>📁 ${proj.name} ${statusBadge}</h4>
        <div class="recent-proj-path">${proj.root_path}</div>
        <div class="recent-proj-meta">
          <span>${proj.total_images || 0} fotos (${proj.processed_images || 0} processadas)</span> &bull;
          <span>Último acesso: ${proj.last_opened ? new Date(proj.last_opened).toLocaleDateString("pt-BR") : "Recentemente"}</span>
        </div>
      `;

      const actions = document.createElement("div");
      actions.className = "recent-proj-actions";

      if (!proj.is_active && proj.exists) {
        const btnOpen = document.createElement("button");
        btnOpen.className = "btn btn-primary btn-xs";
        btnOpen.textContent = "Abrir";
        btnOpen.addEventListener("click", () => openProjectByPath(proj.root_path));
        actions.appendChild(btnOpen);
      }

      const btnRemove = document.createElement("button");
      btnRemove.className = "btn btn-outline btn-xs";
      btnRemove.textContent = "🗑️";
      btnRemove.title = "Remover do histórico de recentes";
      btnRemove.addEventListener("click", async () => {
        await fetch("/api/projects/remove-recent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ root_path: proj.root_path })
        });
        await loadProjectsAndWorkspace(imageSelect ? imageSelect.value : null, true);
      });
      actions.appendChild(btnRemove);

      card.appendChild(info);
      card.appendChild(actions);
      recentProjectsList.appendChild(card);
    });
  }

  async function loadProjectsAndWorkspace(preferredImage = null, skipCanvasLoad = false) {
    try {
      const resp = await fetch("/api/projects");
      const data = await resp.json();

      if (!data.success) {
        console.error("Falha ao obter dados do projeto:", data.error);
        return;
      }

      activeWorkspace = data.workspace;
      workspaceImages = data.images || [];
      workspaceImages.forEach((img) => {
        if (
          img.quadrat_corners &&
          Array.isArray(img.quadrat_corners) &&
          img.quadrat_corners.length === 4 &&
          !quadratCornersByImage[img.filename]
        ) {
          quadratCornersByImage[img.filename] = img.quadrat_corners;
        }
      });

      // Update Header & Sidebar UI
      if (headerProjectName) headerProjectName.textContent = activeWorkspace.name;
      if (sidebarProjectName) sidebarProjectName.textContent = activeWorkspace.name;
      if (sidebarProjectType) {
        sidebarProjectType.textContent = activeWorkspace.is_demo ? "DEMO" : "PROJETO";
        sidebarProjectType.className = `project-tag ${activeWorkspace.is_demo ? "" : "tag-user-proj"}`;
      }
      if (sidebarProjectPath) {
        sidebarProjectPath.textContent = activeWorkspace.root_path;
        sidebarProjectPath.title = activeWorkspace.root_path;
      }
      if (activeProjectFooterLabel) {
        activeProjectFooterLabel.textContent = `Projeto Ativo: ${activeWorkspace.name} (${activeWorkspace.root_path})`;
      }
      if (btnDownloadProjCsv) {
        btnDownloadProjCsv.style.display = activeWorkspace.is_demo ? "none" : "inline-block";
      }

      // Update Summary Badges
      const summary = data.summary || { total: 0, processed: 0, unprocessed: 0, hash_mismatch: 0 };
      if (countProcessedBadge) countProcessedBadge.textContent = `✅ ${summary.processed} processadas`;
      if (countPendingBadge) countPendingBadge.textContent = `⏳ ${summary.unprocessed} pendentes`;
      if (countMismatchBadge) {
        if (summary.hash_mismatch > 0) {
          countMismatchBadge.style.display = "inline-flex";
          countMismatchBadge.textContent = `⚠️ ${summary.hash_mismatch} alteradas`;
        } else {
          countMismatchBadge.style.display = "none";
        }
      }

      if (btnBatchPending) {
        btnBatchPending.textContent = `⚡ Lote: Pendentes (${summary.unprocessed})`;
        btnBatchPending.disabled = summary.unprocessed === 0 && summary.hash_mismatch === 0;
      }

      // Repopulate Image Selector
      if (imageSelect) {
        const prevVal = imageSelect.value;
        imageSelect.innerHTML = "";
        if (workspaceImages.length === 0) {
          imageSelect.innerHTML = "<option value=''>Nenhuma foto neste projeto</option>";
        } else {
          workspaceImages.forEach((img) => {
            const opt = document.createElement("option");
            opt.value = img.filename;
            const statusIcon = img.status === "processed" ? "✅" : (img.status === "hash_mismatch" ? "⚠️" : "⏳");
            opt.textContent = `${statusIcon} ${img.filename} (${img.size_mb} MB)`;
            imageSelect.appendChild(opt);
          });
        }

        // Determine which image to select
        let target = null;
        const urlParams = new URLSearchParams(window.location.search);
        const requestedImg = urlParams.get("image");
        if (requestedImg && workspaceImages.some((i) => i.filename === requestedImg)) {
          target = requestedImg;
        } else if (preferredImage && workspaceImages.some((i) => i.filename === preferredImage)) {
          target = preferredImage;
        } else if (prevVal && workspaceImages.some((i) => i.filename === prevVal)) {
          target = prevVal;
        } else if (workspaceImages.length > 0) {
          target = workspaceImages[0].filename;
        }

        if (target) {
          imageSelect.value = target;
        }
      }

      renderPhotoChecklist();
      renderThumbnailStrip();
      renderRecentProjects(data.recent_projects || []);

      if (imageSelect && imageSelect.value && !skipCanvasLoad) {
        await showImageInStage(imageSelect.value);

        const urlParams = new URLSearchParams(window.location.search);
        const highlightId = urlParams.get("highlight");
        if (highlightId && state.polygonData && state.polygonData.colonies) {
          const colId = parseInt(highlightId, 10);
          const col = state.polygonData.colonies.find((c) => c.id === colId);
          if (col) {
            const polyEl = document.querySelector(`.colony-polygon[data-id="${colId}"]`);
            if (polyEl) {
              polyEl.classList.add("selected-colony");
              const stageRect = interactiveStage.getBoundingClientRect();
              colonyTooltip.innerHTML = `
                <div class="tooltip-genus">
                  <span class="tooltip-color-dot" style="background-color: ${col.color};"></span>
                  #${col.id} ${col.genus}
                </div>
                <div>Área Real: <strong>${col.area_cm2} cm²</strong> (${col.area_pct}%)</div>
                <div>🧠 BioCLIP + Few-Shot: <strong>${(col.confidence * 100).toFixed(1)}%</strong></div>
                <div style="font-size: 0.7rem; color: #38bdf8; margin-top: 2px;">Clique p/ editar ou ajustar borda &bull; Shift+Clique p/ agrupar</div>
              `;
              colonyTooltip.style.display = "block";
              colonyTooltip.style.left = `${stageRect.width * 0.48}px`;
              colonyTooltip.style.top = `${stageRect.height * 0.16}px`;
            }
          }
        }
      }
    } catch (err) {
      console.error("Erro ao carregar projeto e fotos:", err);
    }
  }

  async function refreshProjectsAndImages(targetImage, skipCanvas = false) {
    await loadProjectsAndWorkspace(targetImage, skipCanvas);
  }

  // Multi-select "Select All" toggle
  if (chkSelectAllPhotos) {
    chkSelectAllPhotos.addEventListener("change", (e) => {
      if (e.target.checked) {
        workspaceImages.forEach((img) => selectedForBatch.add(img.filename));
      } else {
        selectedForBatch.clear();
      }
      renderPhotoChecklist();
    });
  }

  if (imageSelect) {
    imageSelect.addEventListener("change", (e) => {
      showingEnhancedBg = false;
      showImageInStage(e.target.value);
    });
  }

  // Uploading photos (supports multiple images at once)
  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      const files = Array.from(e.target.files);
      if (!files || files.length === 0) return;

      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      try {
        const resp = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await resp.json();
        if (data.success) {
          const firstUploaded = (data.uploaded && data.uploaded[0]) ? data.uploaded[0].filename : data.filename;
          await loadProjectsAndWorkspace(firstUploaded);
        } else {
          alert(data.error || "Erro ao enviar imagens.");
        }
      } catch (err) {
        alert("Falha no upload das fotos.");
      } finally {
        fileInput.value = "";
      }
    });
  }

  // Project Modals & Navigation
  function openProjectsModal(tabId = "tab-recent-projects") {
    if (!projectsModal) return;
    projectsModal.style.display = "flex";
    switchModalTab(tabId);
  }

  function closeProjectsModal() {
    if (projectsModal) projectsModal.style.display = "none";
  }

  function switchModalTab(tabId) {
    document.querySelectorAll(".modal-tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabId);
    });
    document.querySelectorAll(".modal-tab-pane").forEach((pane) => {
      pane.classList.toggle("active", pane.id === tabId);
    });
  }

  document.querySelectorAll(".modal-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchModalTab(btn.dataset.tab));
  });

  if (projectHeaderPill) projectHeaderPill.addEventListener("click", () => openProjectsModal());
  if (btnOpenProjects) btnOpenProjects.addEventListener("click", () => openProjectsModal());
  if (btnQuickProjects) btnQuickProjects.addEventListener("click", () => openProjectsModal());
  if (btnCloseProjects) btnCloseProjects.addEventListener("click", closeProjectsModal);
  if (btnModalCloseFooter) btnModalCloseFooter.addEventListener("click", closeProjectsModal);

  if (projectsModal) {
    projectsModal.addEventListener("click", (e) => {
      if (e.target === projectsModal) closeProjectsModal();
    });
  }

  // Native Folder Picker integration (Windows Explorer dialog via Python backend)
  async function pickFolderNative(targetInput) {
    try {
      const resp = await fetch("/api/projects/pick-folder", { method: "POST" });
      const data = await resp.json();
      if (data.success && data.path) {
        targetInput.value = data.path;
      } else if (data.cancelled) {
        // User cancelled dialog, do nothing
      } else if (data.error) {
        alert(`Não foi possível abrir o seletor nativo: ${data.error}\nVocê pode digitar o caminho manualmente.`);
      }
    } catch (err) {
      console.warn("Seletor nativo de pasta:", err);
    }
  }

  if (btnPickFolderNew && newProjectRoot) {
    btnPickFolderNew.addEventListener("click", () => pickFolderNative(newProjectRoot));
  }
  if (btnPickFolderOpen && openProjectRoot) {
    btnPickFolderOpen.addEventListener("click", () => pickFolderNative(openProjectRoot));
  }

  // Create Project
  if (btnCreateProjectSubmit) {
    btnCreateProjectSubmit.addEventListener("click", async () => {
      const name = (newProjectName ? newProjectName.value : "").trim();
      const rootPath = (newProjectRoot ? newProjectRoot.value : "").trim();
      const copySamples = chkCopySamples ? chkCopySamples.checked : true;

      if (!rootPath) {
        alert("Por favor, selecione ou digite a pasta raiz para o novo projeto.");
        return;
      }

      btnCreateProjectSubmit.disabled = true;
      btnCreateProjectSubmit.textContent = "Criando estrutura do projeto...";

      try {
        const resp = await fetch("/api/projects/create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, root_path: rootPath, copy_sample_images: copySamples })
        });
        const data = await resp.json();
        if (!data.success) {
          throw new Error(data.error || "Falha ao criar projeto.");
        }

        closeProjectsModal();
        await loadProjectsAndWorkspace();
        alert(`✅ Projeto '${data.created.name}' criado e ativado com sucesso em:\n${data.created.root_path}`);
      } catch (err) {
        alert(`Erro ao criar projeto:\n${err.message}`);
      } finally {
        btnCreateProjectSubmit.disabled = false;
        btnCreateProjectSubmit.textContent = "✨ Criar e Abrir Projeto";
      }
    });
  }

  // Open Existing Project
  async function openProjectByPath(rootPath) {
    if (!rootPath) return;
    try {
      const resp = await fetch("/api/projects/open", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root_path: rootPath })
      });
      const data = await resp.json();
      if (!data.success) {
        throw new Error(data.error || "Falha ao abrir projeto.");
      }
      closeProjectsModal();
      await loadProjectsAndWorkspace();
    } catch (err) {
      alert(`Erro ao abrir projeto:\n${err.message}`);
    }
  }

  if (btnOpenProjectSubmit) {
    btnOpenProjectSubmit.addEventListener("click", async () => {
      const rootPath = (openProjectRoot ? openProjectRoot.value : "").trim();
      if (!rootPath) {
        alert("Por favor, selecione ou digite a pasta do projeto.");
        return;
      }
      await openProjectByPath(rootPath);
    });
  }

  // Activate Demo Mode
  if (btnActivateDemo) {
    btnActivateDemo.addEventListener("click", async () => {
      try {
        const resp = await fetch("/api/projects/demo", { method: "POST" });
        const data = await resp.json();
        if (data.success) {
          closeProjectsModal();
          await loadProjectsAndWorkspace();
        }
      } catch (err) {
        alert("Falha ao ativar o modo demonstração.");
      }
    });
  }

  // Download Consolidated CSV of the entire project
  if (btnDownloadProjCsv) {
    btnDownloadProjCsv.addEventListener("click", () => {
      window.open("/api/projects/download-summary", "_blank");
    });
  }

  // =========================================================================
  // BATCH PROCESSING PIPELINE (ALL, PENDING, OR SELECTED)
  // =========================================================================
  async function runBatchProcessing(mode) {
    if (isBatchRunning) return;

    let targetFilenames = [];
    if (mode === "selected") {
      targetFilenames = Array.from(selectedForBatch);
      if (targetFilenames.length === 0) {
        alert("Selecione pelo menos uma foto nas caixas de seleção da lista para processar.");
        return;
      }
    } else if (mode === "pending") {
      targetFilenames = workspaceImages
        .filter((img) => img.status === "unprocessed" || img.status === "hash_mismatch")
        .map((img) => img.filename);
      if (targetFilenames.length === 0) {
        alert("Nenhuma foto pendente ou alterada encontrada no projeto!");
        return;
      }
    } else {
      // mode === "all"
      targetFilenames = workspaceImages.map((img) => img.filename);
      if (targetFilenames.length === 0) {
        alert("Nenhuma foto disponível no projeto.");
        return;
      }
    }

    const colabUrl = colabUrlInput ? colabUrlInput.value.trim() : "";
    if (colabUrl) localStorage.setItem("coralscop_colab_url", colabUrl);

    // Open Batch Progress Modal
    if (batchProgressModal) batchProgressModal.style.display = "flex";
    if (btnCloseBatchModal) btnCloseBatchModal.style.display = "none";
    if (btnFinishBatch) btnFinishBatch.style.display = "none";
    if (btnCancelBatch) btnCancelBatch.style.display = "none";

    if (batchModalTitle) {
      batchModalTitle.textContent = `Processamento em Lote (${mode === "pending" ? "Pendentes" : mode === "selected" ? "Selecionadas" : "Todas"})`;
    }
    if (batchModalSubtitle) {
      batchModalSubtitle.textContent = `Executando CoralSCOP ViT-B e BioCLIP 2.5 ReefNet em ${targetFilenames.length} fotos...`;
    }

    if (batchProgressCount) batchProgressCount.textContent = `0 de ${targetFilenames.length} fotos`;
    if (batchProgressPercent) batchProgressPercent.textContent = "0%";
    if (batchProgressBarFill) batchProgressBarFill.style.width = "0%";
    if (batchCurrentImage) batchCurrentImage.textContent = "Iniciando fila no servidor...";

    // Populate initial checklist rows
    if (batchChecklist) {
      batchChecklist.innerHTML = "";
      targetFilenames.forEach((fn, idx) => {
        const row = document.createElement("div");
        row.className = "batch-check-row status-waiting";
        row.id = `batch-row-${idx}`;
        row.innerHTML = `
          <span>📷 ${fn}</span>
          <span class="batch-status-pill badge-pending" id="batch-row-pill-${idx}">Aguardando</span>
        `;
        batchChecklist.appendChild(row);
      });
    }

    isBatchRunning = true;

    // Collect pipeline parameters
    const minArea = minAreaInput
      ? parseInt(minAreaInput.value, 10) || parseInt(minAreaSlider.value, 10)
      : parseInt(minAreaSlider.value, 10);
    const iouThresh = parseFloat(iouSlider.value);
    const quadratWVal = parseFloat(quadratW.value) || 50;
    const quadratHVal = parseFloat(quadratH.value) || 50;
    const filterMode = filterModeSelect ? filterModeSelect.value : "combined";
    const pointsPerSide = samPointsPerSide ? parseInt(samPointsPerSide.value, 10) : 32;
    const predIou = samPredIouSlider ? parseFloat(samPredIouSlider.value) : 0.72;
    const stabilityScore = samStabilitySlider ? parseFloat(samStabilitySlider.value) : 0.62;
    const cropLayers = samCropLayers ? parseInt(samCropLayers.value, 10) : 1;
    const cropDownscale = samCropDownscale ? parseInt(samCropDownscale.value, 10) : 2;

    try {
      if (batchCurrentImage) batchCurrentImage.textContent = `Enviando ${targetFilenames.length} fotos para processamento...`;

      const resp = await fetch("/api/process/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          images: targetFilenames,
          colab_url: colabUrl,
          min_area: minArea,
          iou_thresh: iouThresh,
          n_points: 5,
          quadrat_width_cm: quadratWVal,
          quadrat_height_cm: quadratHVal,
          filter_mode: filterMode,
          quadrat_corners_by_image: quadratCornersByImage,
          points_per_side: pointsPerSide,
          pred_iou_thresh: predIou,
          stability_score_thresh: stabilityScore,
          crop_n_layers: cropLayers,
          crop_n_points_downscale_factor: cropDownscale
        })
      });

      const json = await resp.json();
      if (!json.success) {
        throw new Error(json.error || "Erro durante o processamento em lote.");
      }

      // Update rows with results
      const resultsList = json.results || [];
      resultsList.forEach((r, idx) => {
        const row = document.getElementById(`batch-row-${idx}`);
        const pill = document.getElementById(`batch-row-pill-${idx}`);
        if (row && pill) {
          if (r.success) {
            row.className = "batch-check-row status-done";
            pill.className = "batch-status-pill badge-processed";
            pill.textContent = `✅ ${r.colonies_count} colônias (${r.coral_cover_pct}% cob.)`;
          } else {
            row.className = "batch-check-row status-error";
            pill.className = "batch-status-pill badge-mismatch";
            pill.textContent = `❌ ${r.error || "Erro"}`;
          }
        }
      });

      if (batchProgressCount) batchProgressCount.textContent = `${json.successful} de ${json.total} processadas com sucesso`;
      if (batchProgressPercent) batchProgressPercent.textContent = "100%";
      if (batchProgressBarFill) batchProgressBarFill.style.width = "100%";
      if (batchCurrentImage) {
        batchCurrentImage.textContent = `Lote concluído! ${json.successful} fotos processadas, ${json.failed} falhas. Planilha consolidada gerada.`;
      }

      if (btnFinishBatch) {
        btnFinishBatch.style.display = "inline-block";
        btnFinishBatch.onclick = async () => {
          if (batchProgressModal) batchProgressModal.style.display = "none";
          selectedForBatch.clear();
          const firstSuccess = resultsList.find((r) => r.success);
          await loadProjectsAndWorkspace(firstSuccess ? firstSuccess.image_name : targetFilenames[0]);
        };
      }
      if (btnCloseBatchModal) btnCloseBatchModal.style.display = "inline-block";
    } catch (err) {
      alert(`Erro no lote:\n${err.message}`);
      if (batchCurrentImage) batchCurrentImage.textContent = `Erro no processamento em lote: ${err.message}`;
      if (btnCloseBatchModal) btnCloseBatchModal.style.display = "inline-block";
    } finally {
      isBatchRunning = false;
    }
  }

  if (btnBatchPending) {
    btnBatchPending.addEventListener("click", () => runBatchProcessing("pending"));
  }
  if (btnBatchSelected) {
    btnBatchSelected.addEventListener("click", () => runBatchProcessing("selected"));
  }
  if (btnBatchAll) {
    btnBatchAll.addEventListener("click", () => {
      if (confirm(`Deseja processar todas as ${workspaceImages.length} fotos do projeto?`)) {
        runBatchProcessing("all");
      }
    });
  }
  if (btnCloseBatchModal) {
    btnCloseBatchModal.addEventListener("click", () => {
      if (batchProgressModal) batchProgressModal.style.display = "none";
    });
  }

  // =========================================================================
  // 9. VIEW MODE TOGGLES, OPACITY & FOOTER TABLE TABS
  // =========================================================================
  btnModeInteractive.addEventListener("click", () => {
    activeViewMode = "interactive";
    btnModeInteractive.classList.add("active");
    btnModeRendered.classList.remove("active");
    interactiveStage.style.display = "flex";
    renderedStage.style.display = "none";
    if (currentResult) opacityControl.style.display = "flex";
    updateVisibilityControlsUi();
  });

  btnModeRendered.addEventListener("click", () => {
    if (!currentResult) return;
    if (isDrawingManualPolygon) exitManualDrawMode();
    activeViewMode = "rendered";
    btnModeRendered.classList.add("active");
    btnModeInteractive.classList.remove("active");
    interactiveStage.style.display = "none";
    renderedStage.style.display = "flex";
    opacityControl.style.display = "none";
    updateVisibilityControlsUi();
  });

  opacitySlider.addEventListener("input", (e) => {
    const val = e.target.value;
    opacityVal.textContent = `${val}%`;
    if (outlineOnlyMode) {
      outlineOnlyMode = false;
      updateVisibilityControlsUi();
    }
    redrawSvgScene();
  });

  function setFooterTab(tabName) {
    activeFooterTab = tabName;
    if (btnTableGroups && btnTableGenera) {
      btnTableGroups.classList.toggle("active", tabName === "groups");
      btnTableGenera.classList.toggle("active", tabName === "genera");
    }
    if (groupsTableWrapper && generaTableWrapper) {
      groupsTableWrapper.style.display = tabName === "groups" ? "block" : "none";
      generaTableWrapper.style.display = tabName === "genera" ? "block" : "none";
    }
  }

  if (btnTableGroups) {
    btnTableGroups.addEventListener("click", () => setFooterTab("groups"));
  }
  if (btnTableGenera) {
    btnTableGenera.addEventListener("click", () => setFooterTab("genera"));
  }

  // =========================================================================
  // 10. RUN CORALSCOP + BIOCLIP 2.5 REEFNET PIPELINE
  // =========================================================================
  btnRun.addEventListener("click", async () => {
    const imageName = imageSelect.value;
    if (!imageName) {
      alert("Selecione uma imagem de transecto.");
      return;
    }

    isPickingQuadrat = false;
    pickingCorners = [];
    polygonsVisible = true;
    outlineOnlyMode = false;
    showDiscardedPolygons = false;
    if (isDrawingManualPolygon) exitManualDrawMode();
    closeColonyEditor();

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
    loadingTitle.textContent = "Segmentando e Classificando Gêneros de Corais...";
    loadingSubtext.textContent = colabUrl
      ? `Filtro '${filterMode.toUpperCase()}' (${roiNote}) ➔ CoralSCOP ViT-B ➔ BioCLIP 2.5 ReefNet (Multi-Escala)...`
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

      if (json.genera) coralGenera = json.genera;
      if (json.class_colors) classColors = json.class_colors;
      populateGenusSelect();

      currentResult = json.data;
      if (currentResult.fewshot_summary) {
        renderFewshotSummary(currentResult.fewshot_summary);
      }
      renderResults(currentResult, false, false);
      await refreshProjectsAndImages(imageName, true);
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
      btnRunText.textContent = "Executar CoralSCOP ➔ BioCLIP 2.5";
    }
  });

  // =========================================================================
  // 11. RENDER ECOLOGICAL RESULTS (CARDS + PER-GROUP FOOTER TABLE + PER-GENUS)
  // =========================================================================
  function renderResults(res, keepEnhancedBg = false, preserveZoom = false) {
    if (!preserveZoom) {
      resetPanZoom();
    }

    currentImageDimensions = { width: res.image_width, height: res.image_height };
    imageNameBadge.textContent = `${res.image_filename} (${res.image_width}x${res.image_height} px)`;
    colonyCountBadge.style.display = "inline-flex";
    colonyCountBadge.textContent = `${res.total_colonies} colônias/grupos (${res.total_coral_cover_pct || 0}% cobertura)`;

    if (res.enhanced_image_filename && res.filter_mode !== "none") {
      enhancedUrlByImage[res.image_filename] = `/output/${res.enhanced_image_filename}?t=${Date.now()}`;
    }

    showingEnhancedBg = Boolean(keepEnhancedBg && enhancedUrlByImage[res.image_filename]);
    updateBgToggleUi();
    updateVisibilityControlsUi();

    if (zoomHud) zoomHud.style.display = "flex";
    renderedImage.src = `/output/${res.output_image_filename}?t=${Date.now()}`;
    stageSvg.setAttribute("viewBox", `0 0 ${res.image_width} ${res.image_height}`);
    stageImage.onload = () => {
      updateQuadratUiState();
      updateVisibilityControlsUi();
      redrawSvgScene();
    };
    const desiredBg =
      showingEnhancedBg && enhancedUrlByImage[res.image_filename]
        ? enhancedUrlByImage[res.image_filename]
        : `/images/${res.image_filename}`;
    if (stageImage.getAttribute("src") !== desiredBg) {
      stageImage.src = desiredBg;
    }
    redrawSvgScene();

    btnDownloadCsv.style.display = "inline-flex";
    btnDownloadCsv.onclick = () => {
      window.location.href = `/api/download/csv/${res.output_csv_filename}?t=${Date.now()}`;
    };

    opacityControl.style.display = activeViewMode === "interactive" ? "flex" : "none";
    interactiveStage.style.display = activeViewMode === "interactive" ? "flex" : "none";
    renderedStage.style.display = activeViewMode === "rendered" ? "flex" : "none";

    resultsPanel.style.display = "block";
    const roiTag = res.has_quadrat_roi ? "Homografia 4-Cantos" : "Foto Inteira";
    const clfTag = res.classifier_model || "BioCLIP 2.5 ReefNet";
    const discNote =
      res.discarded_count > 0 ? ` | Não-Coral Ocultos: ${res.discarded_count}` : "";
    resultsMeta.textContent = `Cobertura Coralínea: ${res.total_coral_cm2} cm² (${res.total_coral_cover_pct}%) em ${res.quadrat_width_cm}x${res.quadrat_height_cm} cm (${roiTag}) | Taxonomia: ${clfTag}${discNote}`;

    const activeColonies = (res.colonies || []).filter((c) => !c.discarded);

    if (btnTableGroups) {
      btnTableGroups.textContent = `📋 Por Colônia / Grupo (${activeColonies.length})`;
    }
    if (btnTableGenera) {
      btnTableGenera.textContent = `📊 Consolidado por Gênero (${(res.genus_summary || []).length})`;
    }
    setFooterTab(activeFooterTab);

    // 1. Top Genus Summary Cards
    coverageBarsGrid.innerHTML = "";
    (res.genus_summary || []).forEach((item) => {
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
          <span>${item.count} colônia(s)/grupo(s)</span>
          <span>${item.area_cm2} cm²</span>
        </div>
      `;

      card.addEventListener("mouseenter", () => highlightGenus(item.genus, true));
      card.addEventListener("mouseleave", () => highlightGenus(item.genus, false));
      coverageBarsGrid.appendChild(card);
    });

    // 2. Primary Footer Table: Coverage & Coral Genus per Individual Colony / Group
    if (groupsTbody) {
      groupsTbody.innerHTML = "";
      let totalPolygonParts = 0;

      activeColonies.forEach((col) => {
        const partsCount = (col.polygons && col.polygons.length) || 1;
        totalPolygonParts += partsCount;
        const isGroup = Boolean(col.is_grouped || partsCount > 1);
        const groupLabel = isGroup ? `Grupo #${col.id}` : `Colônia #${col.id}`;
        const partsBadge = isGroup
          ? `<span class="group-badge-pill">🔗 ${partsCount} polígonos</span>`
          : col.is_manual_drawn
          ? `<span class="manual-badge-pill">✍️ 1 polígono manual</span>`
          : `<span class="single-part-pill">1 polígono${col.is_geometry_edited ? " ✒️" : ""}</span>`;

        let srcText = "🤖 BioCLIP 2.5";
        if (col.is_manual_drawn) {
          srcText = col.has_embedding === false ? "✍️ Manual (Offline)" : "✍️ Manual + BioCLIP";
        } else if (col.is_grouped) {
          srcText = "🔗 Agrupado";
        } else if (col.manual_locked) {
          srcText = "✏️ Confirmado";
        } else if (col.used_fewshot) {
          srcText = "🧠 Few-Shot";
        }
        if (col.is_geometry_edited && !col.is_manual_drawn) {
          srcText += " ✒️";
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="species-color-swatch" style="background-color: ${col.color};"></span></td>
          <td><strong>${groupLabel}</strong></td>
          <td><strong>${col.genus}</strong></td>
          <td>${partsBadge}</td>
          <td>${srcText} (${(col.confidence * 100).toFixed(0)}%)</td>
          <td>${col.area_cm2} cm²</td>
          <td><strong>${col.area_pct}%</strong></td>
          <td>
            <button type="button" class="btn btn-outline btn-xs btn-focus-colony">🎯 Editar</button>
          </td>
        `;

        const focusBtn = tr.querySelector(".btn-focus-colony");
        if (focusBtn) {
          focusBtn.addEventListener("click", () => {
            if (activeViewMode !== "interactive") {
              btnModeInteractive.click();
            }
            if (!polygonsVisible) {
              polygonsVisible = true;
              updateVisibilityControlsUi();
              redrawSvgScene();
            }
            openColonyEditor(col, 0);
            viewerContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
          });
        }

        tr.addEventListener("mouseenter", () => highlightSingleColony(col.id, true));
        tr.addEventListener("mouseleave", () => highlightSingleColony(col.id, false));
        groupsTbody.appendChild(tr);
      });

      if (groupsTfoot) {
        groupsTfoot.innerHTML = `
          <tr>
            <td></td>
            <td colspan="2">TOTAL CORALÍNEO (${activeColonies.length} colônias/grupos)</td>
            <td>${totalPolygonParts} polígonos</td>
            <td>11 Gêneros (Estrito)</td>
            <td>${res.total_coral_cm2} cm²</td>
            <td>${res.total_coral_cover_pct}%</td>
            <td></td>
          </tr>
        `;
      }
    }

    // 3. Secondary Footer Table: Consolidated Coverage per Coral Genus
    if (speciesTbody) {
      speciesTbody.innerHTML = "";
      (res.genus_summary || []).forEach((item) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="species-color-swatch" style="background-color: ${item.color};"></span></td>
          <td><strong>${item.genus}</strong></td>
          <td>${item.count}</td>
          <td>${item.area_cm2} cm²</td>
          <td><strong>${item.coverage_pct}%</strong></td>
          <td>
            <button type="button" class="btn btn-outline btn-xs" onclick="filterByGenus('${item.genus}')">Destacar</button>
          </td>
        `;
        tr.addEventListener("mouseenter", () => highlightGenus(item.genus, true));
        tr.addEventListener("mouseleave", () => highlightGenus(item.genus, false));
        speciesTbody.appendChild(tr);
      });
    }
  }

  // Tooltip & Highlight Helpers
  function showTooltip(e, col, partIdx = 0, totalParts = 1) {
    if (col.discarded) {
      colonyTooltip.innerHTML = `
        <div class="tooltip-genus">
          <span class="tooltip-color-dot" style="background-color: #94a3b8;"></span>
          #${col.id} Não é Coral (Descartado)
        </div>
        <div>Área ignorada: ${col.area_cm2} cm²</div>
        <div style="font-size: 0.7rem; color: #7dd3fc; margin-top: 2px;">Clique para restaurar se for um coral real</div>
      `;
    } else {
      const titlePrefix = col.is_grouped || totalParts > 1 ? `Grupo #${col.id}` : `#${col.id}`;
      const partsNote =
        totalParts > 1 ? ` &bull; Parte #${partIdx + 1} de ${totalParts}` : "";
      let srcLabel = col.is_manual_drawn
        ? col.has_embedding === false
          ? "✍️ Manual (Offline)"
          : "✍️ Manual + BioCLIP 2.5"
        : col.is_grouped
        ? "🔗 Grupo Confirmado"
        : col.manual_locked
        ? "✏️ Confirmado"
        : col.used_fewshot
        ? "🧠 BioCLIP + Few-Shot"
        : "🤖 BioCLIP 2.5";
      if (col.is_geometry_edited && !col.is_manual_drawn) {
        srcLabel += " (Borda Editada)";
      }

      colonyTooltip.innerHTML = `
        <div class="tooltip-genus">
          <span class="tooltip-color-dot" style="background-color: ${col.color};"></span>
          ${titlePrefix} ${col.genus}
        </div>
        <div>Área Real: <strong>${col.area_cm2} cm²</strong> (${col.area_pct}%${partsNote})</div>
        <div>${srcLabel}: <strong>${(col.confidence * 100).toFixed(1)}%</strong></div>
        <div style="font-size: 0.7rem; color: #38bdf8; margin-top: 2px;">Clique p/ editar ou ajustar borda &bull; Shift+Clique p/ agrupar</div>
      `;
    }
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
    if (!polygonsVisible) return;
    const normalAlpha = outlineOnlyMode ? 0.0 : opacitySlider.value / 100.0;
    document.querySelectorAll(".colony-polygon").forEach((poly) => {
      if (poly.getAttribute("data-discarded") === "1") return;
      if (
        poly.classList.contains("selected-colony") ||
        poly.classList.contains("group-selected-colony")
      ) {
        return;
      }
      if (active) {
        if (poly.getAttribute("data-genus") === genus) {
          poly.style.stroke = "#ffffff";
          poly.style.strokeWidth = "7px";
          poly.style.fillOpacity = outlineOnlyMode ? "0.2" : "0.78";
        } else {
          poly.style.fillOpacity = outlineOnlyMode ? "0.0" : "0.06";
        }
      } else {
        poly.style.stroke = "";
        poly.style.strokeWidth = "";
        poly.style.fillOpacity = normalAlpha;
      }
    });
  }

  function highlightSingleColony(colonyId, active) {
    if (!polygonsVisible) return;
    const normalAlpha = outlineOnlyMode ? 0.0 : opacitySlider.value / 100.0;
    document.querySelectorAll(".colony-polygon").forEach((poly) => {
      if (poly.getAttribute("data-discarded") === "1") return;
      if (
        poly.classList.contains("selected-colony") ||
        poly.classList.contains("group-selected-colony")
      ) {
        return;
      }
      const cid = parseInt(poly.getAttribute("data-id"), 10);
      if (active) {
        if (cid === colonyId) {
          poly.style.stroke = "#ffffff";
          poly.style.strokeWidth = "8px";
          poly.style.fillOpacity = outlineOnlyMode ? "0.25" : "0.82";
        } else {
          poly.style.fillOpacity = outlineOnlyMode ? "0.0" : "0.06";
        }
      } else {
        poly.style.stroke = "";
        poly.style.strokeWidth = "";
        poly.style.fillOpacity = normalAlpha;
      }
    });
  }

  window.filterByGenus = function (genus) {
    highlightGenus(genus, true);
    setTimeout(() => {
      highlightGenus(genus, false);
    }, 2500);
  };

  // =========================================================================
  // 12. LOG VIEWER MODAL
  // =========================================================================
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

  // =========================================================================
  // VS CODE STYLE SIDEBAR ACTIVITY TABS
  // =========================================================================
  const activityTabBtns = document.querySelectorAll(".activity-tab-btn");
  const sidebarTabPanes = document.querySelectorAll(".sidebar-tab-pane");

  function switchTab(targetTabId) {
    const targetPaneId = targetTabId.replace("tab-", "tab-pane-");
    activityTabBtns.forEach((b) => b.classList.toggle("active", b.dataset.tab === targetTabId));
    sidebarTabPanes.forEach((p) => p.classList.toggle("active", p.id === targetPaneId));
  }

  activityTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab);
    });
  });

  if (window.location.hash) {
    const hash = window.location.hash.replace("#", "");
    if (document.getElementById(hash.replace("tab-", "tab-pane-"))) {
      switchTab(hash);
    }
  }

  // Initial load
  loadTaxonomyAndFewshot();
  loadProjectsAndWorkspace();
});
