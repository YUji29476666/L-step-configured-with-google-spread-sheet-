// config.gs - GAS 設定管理
// このファイルを Google Sheets の Apps Script エディタにコピー＆ペーストしてください

function getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    SPREADSHEET_ID: props.getProperty('SPREADSHEET_ID'),
    GITHUB_TOKEN: props.getProperty('GITHUB_TOKEN'),
    GITHUB_REPO: props.getProperty('GITHUB_REPO'),
    RAW_SHEET_NAME: props.getProperty('RAW_SHEET_NAME') || 'raw',
    CLEANED_SHEET_NAME: props.getProperty('CLEANED_SHEET_NAME') || 'cleaned',
    LOG_SHEET_NAME: props.getProperty('LOG_SHEET_NAME') || 'log',
    WORKFLOW_NAME: props.getProperty('WORKFLOW_NAME') || 'normalize.yml',
    POLL_INTERVAL_SEC: parseInt(props.getProperty('POLL_INTERVAL_SEC') || '10'),
    MAX_WAIT_SEC: parseInt(props.getProperty('MAX_WAIT_SEC') || '300')  // 5分
  };
}

function setupScriptProperties() {
  const ui = SpreadsheetApp.getUi();
  
  // Spreadsheet ID 入力
  const spreadsheetIdResponse = ui.prompt('Spreadsheet ID を入力してください\n例：1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo');
  
  if (spreadsheetIdResponse.getSelectedButton() === ui.Button.OK) {
    const props = PropertiesService.getScriptProperties();
    props.setProperty('SPREADSHEET_ID', spreadsheetIdResponse.getResponseText());
    
    // GitHub リポジトリ入力
    const repoResponse = ui.prompt('GitHub リポジトリを入力してください\n例：YUji29476666/lstep-data');
    if (repoResponse.getSelectedButton() === ui.Button.OK) {
      props.setProperty('GITHUB_REPO', repoResponse.getResponseText());
    }
    
    ui.alert('✅ 設定を保存しました\n\n次に、GAS プロジェクト設定で「スクリプト プロパティ」から\n手動で GITHUB_TOKEN を設定してください\n\n設定手順：\n1. Apps Script エディタのメニュー → プロジェクトの設定\n2. 「スクリプト プロパティ」タブ\n3. 新しい行を追加\n4. キー: GITHUB_TOKEN\n5. 値: 実際の GitHub トークン\n6. 保存');
  }
}

function showConfig() {
  const config = getConfig();
  const message = `
========== 現在の設定 ==========
Spreadsheet ID: ${config.SPREADSHEET_ID || '未設定'}
GitHub リポジトリ: ${config.GITHUB_REPO || '未設定'}
GitHub トークン: ${config.GITHUB_TOKEN ? '✅ 設定済み' : '❌ 未設定'}
Raw シート: ${config.RAW_SHEET_NAME}
Cleaned シート: ${config.CLEANED_SHEET_NAME}
Log シート: ${config.LOG_SHEET_NAME}
Workflow: ${config.WORKFLOW_NAME}
================================
  `.trim();
  
  SpreadsheetApp.getUi().alert(message);
}
