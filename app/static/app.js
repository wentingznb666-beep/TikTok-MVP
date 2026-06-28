/**
 * app.js — 主页面交互逻辑
 * TikTok 电商卖家助手 MVP
 */

// ═══════════════════════════════════════════════════════════════
// 全局状态
// ═══════════════════════════════════════════════════════════════

let state = {
  token: localStorage.getItem('auth_token'),
  username: localStorage.getItem('username'),
  currentMainTab: 'analyze',
  inputMethod: 'text',        // 'text' | 'video' | 'image'
  videoFile: null,
  imageFile: null,
  translateDirection: 'zh2th',
  currentDetail: null,        // 当前查看的分析详情
};

// ═══════════════════════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  // 鉴权检查
  if (!state.token) {
    window.location.href = '/static/login.html';
    return;
  }

  // 验证 token
  fetch('/api/auth/me', {
    headers: { 'Authorization': 'Bearer ' + state.token }
  }).then(r => {
    if (!r.ok) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('username');
      window.location.href = '/static/login.html';
    }
  });

  // 显示用户名
  document.getElementById('usernameDisplay').textContent = state.username || '';

  // 监听文本字数
  const textarea = document.getElementById('copyText');
  if (textarea) {
    textarea.addEventListener('input', () => {
      document.getElementById('charCount').textContent = textarea.value.length;
    });
  }

  // 加载历史记录
  loadHistory();
});

// ═══════════════════════════════════════════════════════════════
// 主 Tab 切换：视频分析 / 翻译
// ═══════════════════════════════════════════════════════════════

function switchMainTab(tab) {
  state.currentMainTab = tab;

  document.querySelectorAll('.main-tab').forEach((btn, i) => {
    btn.classList.toggle('active', (i === 0 && tab === 'analyze') || (i === 1 && tab === 'translate'));
  });

  document.getElementById('analyzePanel').style.display = tab === 'analyze' ? 'flex' : 'none';
  document.getElementById('translatePanel').style.display = tab === 'translate' ? 'block' : 'none';

  if (tab === 'analyze') {
    loadHistory();
  }
}

// ═══════════════════════════════════════════════════════════════
// 输入方式切换：文案 / 视频 / 图片
// ═══════════════════════════════════════════════════════════════

function switchInputMethod(method) {
  state.inputMethod = method;

  document.querySelectorAll('.method-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.method === method);
  });

  // 显示/隐藏对应输入区域
  document.getElementById('textInputArea').style.display = (method === 'text' || method === 'image') ? 'block' : 'none';
  document.getElementById('videoUploadArea').style.display = method === 'video' ? 'block' : 'none';
  document.getElementById('imageUploadArea').style.display = method === 'image' ? 'block' : 'none';

  // 图片模式下文案和图片都显示
  if (method === 'video') {
    // 纯视频模式：不需要文案区域
  }
}

// ═══════════════════════════════════════════════════════════════
// 文件上传处理
// ═══════════════════════════════════════════════════════════════

function onFileSelected(type) {
  const input = document.getElementById(type === 'video' ? 'videoInput' : 'imageInput');
  const file = input.files[0];
  if (!file) return;

  if (type === 'video') {
    state.videoFile = file;
    document.getElementById('videoFileName').textContent = file.name;
    document.getElementById('videoFileInfo').style.display = 'flex';
    document.getElementById('videoDropZone').style.display = 'none';
  } else {
    state.imageFile = file;
    document.getElementById('imageFileName').textContent = file.name;
    document.getElementById('imageFileInfo').style.display = 'flex';
    document.getElementById('imageDropZone').style.display = 'none';
  }
}

function clearFile(type) {
  if (type === 'video') {
    state.videoFile = null;
    document.getElementById('videoInput').value = '';
    document.getElementById('videoFileInfo').style.display = 'none';
    document.getElementById('videoDropZone').style.display = 'block';
  } else {
    state.imageFile = null;
    document.getElementById('imageInput').value = '';
    document.getElementById('imageFileInfo').style.display = 'none';
    document.getElementById('imageDropZone').style.display = 'block';
  }
}

// ═══════════════════════════════════════════════════════════════
// 执行分析
// ═══════════════════════════════════════════════════════════════

async function doAnalyze() {
  const copyText = document.getElementById('copyText').value.trim();
  const videoFile = state.videoFile;
  const imageFile = state.imageFile;

  // 校验至少有一种输入
  if (!copyText && !videoFile) {
    alert(t('errNoInput'));
    return;
  }

  // 构建 FormData
  const formData = new FormData();
  if (copyText) {
    formData.append('copy_text', copyText);
  }
  if (videoFile) {
    // 客户端校验
    const maxSize = 100 * 1024 * 1024;
    if (videoFile.size > maxSize) {
      alert(t('errFileTooLarge'));
      return;
    }
    formData.append('video', videoFile);
  }
  if (imageFile) {
    formData.append('image', imageFile);
  }

  // UI 状态
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.style.display = 'none';
  document.getElementById('loadingSpinner').style.display = 'block';
  document.getElementById('resultContainer').style.display = 'none';

  try {
    const r = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + state.token },
      body: formData,
    });

    const data = await r.json();

    if (!r.ok || !data.success) {
      alert(data.detail || data.message || t('errAnalysis'));
      return;
    }

    // 渲染结果
    renderAnalysisResult(data.analysis);
    state.currentDetail = data;

    // 刷新历史
    loadHistory();

  } catch (err) {
    alert(t('errNetwork') + ': ' + err.message);
  } finally {
    btn.disabled = false;
    btn.style.display = 'block';
    document.getElementById('loadingSpinner').style.display = 'none';
  }
}

// ═══════════════════════════════════════════════════════════════
// 渲染分析结果（6 维度）
// ═══════════════════════════════════════════════════════════════

function renderAnalysisResult(analysis) {
  const container = document.getElementById('resultContainer');
  container.style.display = 'block';

  if (!analysis || analysis.parse_error) {
    container.innerHTML = `<div class="card"><pre style="white-space:pre-wrap;font-size:13px;">${escapeHtml(analysis?.raw_analysis || '分析结果为空')}</pre></div>`;
    return;
  }

  let html = `<div class="card"><div class="card-title" data-i18n="resultTitle">📋 分析报告</div></div>`;

  // 维度 1：视频结构拆解
  if (analysis.structure) {
    html += buildDimSection(t('dim1'), t('dim1'), [
      { label: t('hook'), value: analysis.structure.hook },
      { label: t('middle'), value: analysis.structure.middle },
      { label: t('cta'), value: analysis.structure.cta },
    ]);
  }

  // 维度 2：话术技巧提炼
  if (analysis.copywriting) {
    html += buildDimSection(t('dim2'), t('dim2'), [
      { label: t('highConversion'), value: listToHtml(analysis.copywriting.high_conversion_sentences) },
      { label: t('interactionQ'), value: listToHtml(analysis.copywriting.interaction_questions) },
      { label: t('emotionCurve'), value: analysis.copywriting.emotion_curve },
    ]);
  }

  // 维度 3：受众与情绪
  if (analysis.audience) {
    html += buildDimSection(t('dim3'), t('dim3'), [
      { label: t('persona'), value: analysis.audience.persona },
      { label: t('emotionalResonance'), value: analysis.audience.emotional_resonance },
    ]);
  }

  // 维度 4：视听配合
  if (analysis.audio_visual) {
    html += buildDimSection(t('dim4'), t('dim4'), [
      { label: t('matchLevel'), value: analysis.audio_visual.match_level },
      { label: t('suggestions'), value: analysis.audio_visual.suggestions },
    ]);
  }

  // 维度 5：差异化亮点与避雷
  if (analysis.highlights) {
    const strengthsHtml = (analysis.highlights.strengths || []).map(s => `<span class="tag good">✨ ${escapeHtml(s)}</span>`).join(' ');
    const warningsHtml = (analysis.highlights.warnings || []).map(w => `<span class="tag warn">⚠️ ${escapeHtml(w)}</span>`).join(' ');
    html += buildDimSection(t('dim5'), t('dim5'), [
      { label: t('strengths'), value: strengthsHtml || '—' },
      { label: t('warnings'), value: warningsHtml || '—' },
    ]);
  }

  // 维度 6：复用优化建议
  if (analysis.optimization) {
    html += buildDimSection(t('dim6'), t('dim6'), [
      { label: t('scriptFramework'), value: analysis.optimization.script_framework },
      { label: t('revisions'), value: listToHtml(analysis.optimization.revisions) },
      { label: t('categorySuggestions'), value: analysis.optimization.category_suggestions },
      { label: t('thaiScript'), value: `<p style="background:rgba(0,210,160,0.08);padding:12px;border-radius:8px;border:1px solid var(--accent);white-space:pre-wrap;">${escapeHtml(analysis.optimization.thai_script || '')}</p>` },
    ]);
  }

  // 分享链接
  if (state.currentDetail && state.currentDetail.share_token) {
    const shareUrl = `${window.location.origin}/api/share/${state.currentDetail.share_token}`;
    html += `
      <div class="card" style="text-align:center;">
        <div style="font-weight:700;margin-bottom:8px;" data-i18n="shareLink">🔗 分享链接</div>
        <div style="display:flex;gap:8px;align-items:center;">
          <input value="${escapeHtml(shareUrl)}" readonly style="flex:1;padding:10px;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px;" id="shareUrlInput">
          <button class="btn-sm" onclick="copyShareLink()" data-i18n="copyLink">复制链接</button>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
  container.scrollIntoView({ behavior: 'smooth' });

  // 更新语言
  updatePageLanguage();
}

function buildDimSection(header, i18nKey, items) {
  let body = '';
  for (const item of items) {
    body += `<p><strong>${item.label}：</strong>${item.value || '—'}</p>`;
  }
  return `
    <div class="dim-section">
      <div class="dim-header">${header}</div>
      <div class="dim-content">${body}</div>
    </div>
  `;
}

function listToHtml(arr) {
  if (!arr || arr.length === 0) return '—';
  return '<ul>' + arr.map(s => `<li>${escapeHtml(s)}</li>`).join('') + '</ul>';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════
// 分享链接复制
// ═══════════════════════════════════════════════════════════════

function copyShareLink() {
  const input = document.getElementById('shareUrlInput');
  if (input) {
    input.select();
    document.execCommand('copy');
    alert('链接已复制！');
  }
}

// ═══════════════════════════════════════════════════════════════
// 加载历史记录
// ═══════════════════════════════════════════════════════════════

async function loadHistory() {
  try {
    const r = await fetch('/api/history', {
      headers: { 'Authorization': 'Bearer ' + state.token }
    });
    const data = await r.json();
    renderHistoryList(data.items || []);
  } catch (err) {
    console.error('加载历史失败:', err);
  }
}

function renderHistoryList(items) {
  const container = document.getElementById('historyList');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="icon">📭</div><div data-i18n="noHistory">暂无分析记录</div></div>`;
    updatePageLanguage();
    return;
  }

  container.innerHTML = items.map(item => `
    <div class="history-item" onclick="loadHistoryDetail('${item.record_id}')">
      <div class="preview">${escapeHtml(item.transcript_preview)}</div>
      <div class="meta">
        <span>${item.created_at || ''}</span>
        <span>${item.has_image ? '🖼️' : '📝'}</span>
      </div>
    </div>
  `).join('');
}

// ═══════════════════════════════════════════════════════════════
// 加载历史详情
// ═══════════════════════════════════════════════════════════════

async function loadHistoryDetail(recordId) {
  try {
    const r = await fetch(`/api/history/${recordId}`, {
      headers: { 'Authorization': 'Bearer ' + state.token }
    });
    const data = await r.json();
    if (data.success) {
      state.currentDetail = { share_token: data.data.share_token };
      // 回填文案
      document.getElementById('copyText').value = data.data.transcript || '';
      document.getElementById('charCount').textContent = (data.data.transcript || '').length;
      // 渲染结果
      renderAnalysisResult(data.data.analysis);
    }
  } catch (err) {
    alert(t('errNotFound'));
  }
}

// ═══════════════════════════════════════════════════════════════
// 翻译功能
// ═══════════════════════════════════════════════════════════════

function switchTranslateDir(dir) {
  state.translateDirection = dir;
  document.querySelectorAll('.direction-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.dir === dir);
  });
}

async function doTranslate() {
  const text = document.getElementById('translateInput').value.trim();
  if (!text) {
    alert('请输入要翻译的文本');
    return;
  }

  const btn = document.getElementById('translateBtn');
  const spinner = document.getElementById('translateSpinner');
  btn.style.display = 'none';
  spinner.style.display = 'block';
  document.getElementById('translateOutput').style.display = 'none';
  document.getElementById('translateResultLabel').style.display = 'none';
  document.getElementById('copyResultBtn').style.display = 'none';

  try {
    const r = await fetch('/api/translate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + state.token,
      },
      body: JSON.stringify({
        text: text,
        direction: state.translateDirection,
      }),
    });

    const data = await r.json();

    if (data.success) {
      document.getElementById('translateOutput').textContent = data.translated_text;
      document.getElementById('translateOutput').style.display = 'block';
      document.getElementById('translateResultLabel').style.display = 'block';
      document.getElementById('copyResultBtn').style.display = 'block';
    } else {
      alert(data.detail || data.message || t('errTranslate'));
    }
  } catch (err) {
    alert(t('errNetwork'));
  } finally {
    btn.style.display = 'block';
    spinner.style.display = 'none';
  }
}

function copyTranslateResult() {
  const text = document.getElementById('translateOutput').textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert('译文已复制！');
  }).catch(() => {
    // 降级方案
    const range = document.createRange();
    range.selectNode(document.getElementById('translateOutput'));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    document.execCommand('copy');
    alert('译文已复制！');
  });
}

// ═══════════════════════════════════════════════════════════════
// 退出登录
// ═══════════════════════════════════════════════════════════════

function doLogout() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('username');
  window.location.href = '/static/login.html';
}
