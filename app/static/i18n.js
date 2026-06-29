/**
 * i18n.js — 中泰双语国际化
 * 全站文本字典，支持 localStorage 记住语言选择
 */

const I18N_DICT = {
  // ── 通用 ────────────────────────────────────────
  zh: {
    appTitle: 'TikTok 电商卖家助手',
    appSubtitle: 'AI 爆款短视频分析工具',
    login: '登录',
    register: '注册',
    username: '用户名',
    password: '密码',
    loginBtn: '登录',
    registerBtn: '注册',
    noAccount: '没有账号？去注册',
    hasAccount: '已有账号？去登录',
    logout: '退出登录',
    copy: '复制',
    share: '分享',
    delete: '删除',
    save: '保存',
    cancel: '取消',
    loading: '加载中...',
    error: '出错了',
    success: '操作成功',
    confirm: '确认',

    // ── 主页 Tab ──────────────────────────────────
    tabAnalyze: '📊 视频分析',
    tabTranslate: '🔄 中泰翻译',
    langSwitch: 'ภาษาไทย',

    // ── 分析页 ────────────────────────────────────
    inputLabel: '输入方式',
    pasteText: '📝 粘贴文案',
    uploadVideo: '🎬 上传视频',
    uploadImage: '🖼️ 上传商品图',
    uploadImageOptional: '(可选)',
    textPlaceholder: '在此粘贴带货视频的口播文案...',
    analyzeBtn: '🔍 开始分析',
    analyzing: '分析中，请稍候...',

    // ── 进度条阶段 ──────────────────────────────
    progressExtracting: '正在提取音频...',
    progressTranscribing: '正在语音转文字...',
    progressAnalyzing: 'AI 正在分析中...',
    progressComplete: '✅ 分析完成',
    dragDrop: '或拖拽文件到此处',
    videoHint: '支持 mp4/mov，最大 100MB',
    imageHint: '支持 jpg/png/webp',

    // ── 分析结果 ──────────────────────────────────
    resultTitle: '📋 分析报告',
    dim1: '1. 视频结构拆解',
    dim2: '2. 话术技巧提炼',
    dim3: '3. 受众与情绪分析',
    dim4: '4. 视听画面配合分析',
    dim5: '5. 差异化亮点与避雷',
    dim6: '6. 复用优化建议',
    hook: '黄金前3秒钩子',
    middle: '中段卖点排布',
    cta: '结尾CTA逼单',
    highConversion: '高转化句式',
    interactionQ: '互动提问',
    emotionCurve: '情绪曲线',
    persona: '目标人群画像',
    emotionalResonance: '情绪共鸣点',
    matchLevel: '文案与画面匹配度',
    suggestions: '配合建议',
    strengths: '差异化亮点',
    warnings: '避雷建议',
    scriptFramework: '通用脚本框架',
    revisions: '修改方案',
    categorySuggestions: '品类扩展建议',
    thaiScript: '🇹🇭 泰语版脚本',
    shareLink: '分享链接',
    copyLink: '复制链接',

    // ── 历史记录 ──────────────────────────────────
    historyTitle: '📜 历史记录',
    noHistory: '暂无分析记录',
    selectAll: '全选',
    deleteSelected: '删除所选',
    clearAllHistory: '全部清除',
    confirmClearAll: '确定要清空全部历史记录吗？此操作不可撤销。',
    noSelection: '请先选择要删除的记录',
    viewDetail: '查看详情',
    created: '创建于',

    // ── 翻译页 ────────────────────────────────────
    translateDirection: '翻译方向',
    zh2th: '中 → 泰',
    th2zh: '泰 → 中',
    translateInput: '输入要翻译的文本...',
    translateBtn: '🔄 翻译',
    clearBtn: '🗑️ 清除',
    translating: '翻译中...',
    translateResult: '翻译结果',
    copyResult: '复制译文',
    speakBtn: '🔊 朗读',

    // ── 错误提示 ──────────────────────────────────
    errNetwork: '网络错误，请检查连接',
    errLogin: '用户名或密码错误',
    errRegister: '注册失败，请重试',
    errNoInput: '请提供文案或上传视频',
    errFileTooLarge: '文件大小超出限制',
    errFileFormat: '不支持的文件格式',
    errAnalysis: '分析失败，请重试',
    errTranslate: '翻译失败，请重试',
    errUnauthorized: '登录已过期，请重新登录',
    errNotFound: '记录不存在或无权访问',
  },

  // ── 泰语 ────────────────────────────────────────
  th: {
    appTitle: 'ผู้ช่วยผู้ขาย TikTok',
    appSubtitle: 'เครื่องมือวิเคราะห์วิดีโอไวรัลด้วย AI',
    login: 'เข้าสู่ระบบ',
    register: 'สมัครสมาชิก',
    username: 'ชื่อผู้ใช้',
    password: 'รหัสผ่าน',
    loginBtn: 'เข้าสู่ระบบ',
    registerBtn: 'สมัครสมาชิก',
    noAccount: 'ยังไม่มีบัญชี? สมัครสมาชิก',
    hasAccount: 'มีบัญชีแล้ว? เข้าสู่ระบบ',
    logout: 'ออกจากระบบ',
    copy: 'คัดลอก',
    share: 'แชร์',
    delete: 'ลบ',
    save: 'บันทึก',
    cancel: 'ยกเลิก',
    loading: 'กำลังโหลด...',
    error: 'เกิดข้อผิดพลาด',
    success: 'ดำเนินการสำเร็จ',
    confirm: 'ยืนยัน',

    tabAnalyze: '📊 วิเคราะห์วิดีโอ',
    tabTranslate: '🔄 แปลภาษา',
    langSwitch: '中文',

    inputLabel: 'วิธีการป้อนข้อมูล',
    pasteText: '📝 วางข้อความ',
    uploadVideo: '🎬 อัปโหลดวิดีโอ',
    uploadImage: '🖼️ อัปโหลดรูปสินค้า',
    uploadImageOptional: '(ไม่จำเป็น)',
    textPlaceholder: 'วางบทพูดวิดีโอของคุณที่นี่...',
    analyzeBtn: '🔍 เริ่มวิเคราะห์',
    analyzing: 'กำลังวิเคราะห์ กรุณารอ...',

    // ── แถบความคืบหน้า ──────────────────────────
    progressExtracting: 'กำลังแยกเสียง...',
    progressTranscribing: 'กำลังแปลงเสียงเป็นข้อความ...',
    progressAnalyzing: 'AI กำลังวิเคราะห์...',
    progressComplete: '✅ วิเคราะห์เสร็จสิ้น',
    dragDrop: 'หรือลากไฟล์มาวางที่นี่',
    videoHint: 'รองรับ mp4/mov สูงสุด 100MB',
    imageHint: 'รองรับ jpg/png/webp',

    resultTitle: '📋 รายงานการวิเคราะห์',
    dim1: '1. การวิเคราะห์โครงสร้างวิดีโอ',
    dim2: '2. เทคนิคการพูด',
    dim3: '3. การวิเคราะห์กลุ่มเป้าหมายและอารมณ์',
    dim4: '4. การวิเคราะห์ภาพและเสียง',
    dim5: '5. จุดเด่นและข้อควรระวัง',
    dim6: '6. คำแนะนำการปรับใช้',
    hook: 'Hook 3 วินาทีแรก',
    middle: 'การจัดวางจุดขาย',
    cta: 'CTA ปิดการขาย',
    highConversion: 'ประโยคที่มีอัตราการแปลงสูง',
    interactionQ: 'คำถามสร้างปฏิสัมพันธ์',
    emotionCurve: 'เส้นโค้งอารมณ์',
    persona: 'โปรไฟล์กลุ่มเป้าหมาย',
    emotionalResonance: 'จุด共鸣ทางอารมณ์',
    matchLevel: 'ความสอดคล้องระหว่างข้อความและภาพ',
    suggestions: 'คำแนะนำ',
    strengths: 'จุดเด่น',
    warnings: 'ข้อควรระวัง',
    scriptFramework: 'กรอบสคริปต์',
    revisions: 'แผนการปรับปรุง',
    categorySuggestions: 'หมวดหมู่ที่แนะนำ',
    thaiScript: '🇹🇭 สคริปต์ภาษาไทย',
    shareLink: 'ลิงก์แชร์',
    copyLink: 'คัดลอกลิงก์',

    historyTitle: '📜 ประวัติ',
    noHistory: 'ยังไม่มีประวัติการวิเคราะห์',
    selectAll: 'เลือกทั้งหมด',
    deleteSelected: 'ลบที่เลือก',
    clearAllHistory: 'ลบทั้งหมด',
    confirmClearAll: 'คุณแน่ใจหรือไม่ว่าต้องการลบประวัติทั้งหมด? การดำเนินการนี้ไม่สามารถยกเลิกได้',
    noSelection: 'กรุณาเลือกรายการที่จะลบก่อน',
    viewDetail: 'ดูรายละเอียด',
    created: 'สร้างเมื่อ',

    translateDirection: 'ทิศทางการแปล',
    zh2th: 'จีน → ไทย',
    th2zh: 'ไทย → จีน',
    translateInput: 'ป้อนข้อความที่ต้องการแปล...',
    translateBtn: '🔄 แปลภาษา',
    clearBtn: '🗑️ ล้าง',
    translating: 'กำลังแปล...',
    translateResult: 'ผลการแปล',
    copyResult: 'คัดลอกผลลัพธ์',
    speakBtn: '🔊 อ่านออกเสียง',

    errNetwork: 'ข้อผิดพลาดเครือข่าย',
    errLogin: 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',
    errRegister: 'การสมัครล้มเหลว',
    errNoInput: 'กรุณาใส่ข้อความหรืออัปโหลดวิดีโอ',
    errFileTooLarge: 'ไฟล์ใหญ่เกินไป',
    errFileFormat: 'รูปแบบไฟล์ไม่รองรับ',
    errAnalysis: 'การวิเคราะห์ล้มเหลว',
    errTranslate: 'การแปลล้มเหลว',
    errUnauthorized: 'เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่',
    errNotFound: 'ไม่พบข้อมูลหรือไม่มีสิทธิ์เข้าถึง',
  }
};

// ── 当前语言状态 ──────────────────────────────────────────────
let currentLang = localStorage.getItem('app_lang') || 'zh';

/**
 * 获取翻译文本
 * @param {string} key — 字典 key
 * @returns {string}
 */
function t(key) {
  return (I18N_DICT[currentLang] && I18N_DICT[currentLang][key]) || key;
}

/**
 * 切换语言并刷新页面文本
 */
function toggleLang() {
  currentLang = currentLang === 'zh' ? 'th' : 'zh';
  localStorage.setItem('app_lang', currentLang);
  updatePageLanguage();
}

/**
 * 更新页面中所有带 data-i18n 属性的元素文本
 */
function updatePageLanguage() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.placeholder = t(key);
    } else {
      el.textContent = t(key);
    }
  });

  // 更新语言切换按钮文字
  const langBtn = document.getElementById('langSwitchBtn');
  if (langBtn) {
    langBtn.textContent = currentLang === 'zh' ? 'ภาษาไทย' : '中文';
  }

  // 动态更新页面标题
  document.title = t('appTitle');

  // 触发语言切换事件，app.js 监听以重渲染分析结果
  document.dispatchEvent(new CustomEvent('langChanged'));
}

// 页面加载时应用语言
document.addEventListener('DOMContentLoaded', updatePageLanguage);
