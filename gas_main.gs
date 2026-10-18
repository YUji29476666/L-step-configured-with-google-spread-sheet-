// main.gs - UI・メイン処理
// このファイルを Google Sheets の Apps Script エディタにコピー＆ペーストしてください

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('lstep データ正規化')
    .addItem('実行', 'execute')
    .addItem('ログをクリア', 'clearLog')
    .addItem('設定を確認', 'showConfig')
    .addToUi();
}

function execute() {
  const config = getConfig();
  const ui = SpreadsheetApp.getUi();
  
  // 設定確認
  if (!config.SPREADSHEET_ID || !config.GITHUB_TOKEN || !config.GITHUB_REPO) {
    ui.alert('❌ 設定が不完全です\n\n「lstep データ正規化」メニュー → 「設定を確認」を実行してください');
    return;
  }
  
  try {
    // 1. ワークフロー起動
    logMessage(config, '▶ ワークフロー起動中...');
    const response = triggerWorkflow(config);
    
    if (!response.ok) {
      logError(config, '❌ ワークフロー起動に失敗: ' + response.error);
      ui.alert('❌ ワークフロー起動に失敗しました\n\nログシートを確認してください');
      return;
    }
    
    logMessage(config, '✅ ワークフロー起動成功');
    
    // 2. ポーリング：完了を待つ
    logMessage(config, '⏳ 処理実行中（Python が実行中です）...');
    ui.alert('✅ ワークフロー起動しました\n\n「log」シートで進捗を確認してください\n\n処理予定時間：1～3分');
    
    // 非同期完了確認は setupTrigger() で定期実行
    // ここでは即座に戻す（ユーザーを待たせないため）
    
  } catch (error) {
    logError(config, '❌ エラー: ' + error.toString());
    ui.alert('❌ エラーが発生しました\n\n' + error.toString());
  }
}

function waitForWorkflowCompletion() {
  // この関数は時間トリガーで定期実行される
  // 処理完了を確認して log に記録
  const config = getConfig();
  
  // 本番では、cleaned シートの行数を確認するなど
  // 処理完了を判定する方法を実装する
  logMessage(config, '(ポーリング確認中...)');
}

function clearLog() {
  const config = getConfig();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logSheet = ss.getSheetByName(config.LOG_SHEET_NAME);
  
  if (!logSheet) {
    SpreadsheetApp.getUi().alert('❌ ログシートが見つかりません: ' + config.LOG_SHEET_NAME);
    return;
  }
  
  logSheet.clearContents();
  logMessage(config, '✅ ログをクリアしました');
}

function logMessage(config, message) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const logSheet = ss.getSheetByName(config.LOG_SHEET_NAME);
    
    if (!logSheet) {
      Logger.log('⚠️ ログシートが見つかりません: ' + config.LOG_SHEET_NAME);
      return;
    }
    
    logSheet.appendRow([
      new Date().toLocaleString('ja-JP'),
      message,
      '情報'
    ]);
  } catch (e) {
    Logger.log('❌ ログ記録エラー: ' + e.toString());
  }
}

function logError(config, message) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const logSheet = ss.getSheetByName(config.LOG_SHEET_NAME);
    
    if (!logSheet) {
      Logger.log('⚠️ ログシートが見つかりません: ' + config.LOG_SHEET_NAME);
      return;
    }
    
    logSheet.appendRow([
      new Date().toLocaleString('ja-JP'),
      message,
      'エラー'
    ]);
  } catch (e) {
    Logger.log('❌ ログ記録エラー: ' + e.toString());
  }
}

function setupTrigger() {
  // 時間トリガーを設定：毎分実行
  // ユーザーが GAS エディタから手動で実行してください
  const triggers = ScriptApp.getProjectTriggers();
  
  // 既存トリガーを削除
  for (let i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  
  // 新規トリガー：毎分
  ScriptApp.newTrigger('waitForWorkflowCompletion')
    .timeBased()
    .everyMinutes(1)
    .create();
  
  SpreadsheetApp.getUi().alert('✅ タイムトリガーを設定しました\n\n毎分、処理完了を確認します');
}
