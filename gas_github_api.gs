// github-api.gs - GitHub API ラッパー
// このファイルを Google Sheets の Apps Script エディタにコピー＆ペーストしてください

function triggerWorkflow(config) {
  // GitHub Actions ワークフロー を起動する
  const url = `https://api.github.com/repos/${config.GITHUB_REPO}/actions/workflows/${config.WORKFLOW_NAME}/dispatches`;
  
  const payload = {
    ref: 'main',
    inputs: {
      spreadsheet_id: config.SPREADSHEET_ID,
      raw_sheet: config.RAW_SHEET_NAME
    }
  };
  
  const options = {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
      'Accept': 'application/vnd.github.v3+json'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true  // エラーレスポンスも取得
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    
    if (responseCode === 204) {
      // 204 No Content = 成功
      return { ok: true };
    } else {
      const content = response.getContentText();
      return { 
        ok: false, 
        error: `HTTP ${responseCode}: ${content.substring(0, 200)}` 
      };
    }
  } catch (error) {
    return { 
      ok: false, 
      error: error.toString() 
    };
  }
}

function checkWorkflowStatus(config, workflowId) {
  // ワークフロー実行の状態を確認する
  // 注：本実装では使用していません（Python が Sheets に直接書き込むため）
  
  const url = `https://api.github.com/repos/${config.GITHUB_REPO}/actions/runs/${workflowId}`;
  
  const options = {
    headers: {
      'Authorization': `Bearer ${config.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json'
    },
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    return {
      status: data.status,
      conclusion: data.conclusion
    };
  } catch (error) {
    return {
      status: 'error',
      error: error.toString()
    };
  }
}

function getRepositoryInfo(config) {
  // リポジトリ情報を取得（動作確認用）
  const url = `https://api.github.com/repos/${config.GITHUB_REPO}`;
  
  const options = {
    headers: {
      'Authorization': `Bearer ${config.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json'
    },
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    
    return {
      ok: true,
      name: data.full_name,
      isPrivate: data.private,
      url: data.html_url
    };
  } catch (error) {
    return {
      ok: false,
      error: error.toString()
    };
  }
}

function testGitHubConnection(config) {
  // GitHub 接続テスト用関数
  // GAS エディタから手動で実行してください
  
  if (!config.GITHUB_TOKEN) {
    SpreadsheetApp.getUi().alert('❌ GITHUB_TOKEN が設定されていません');
    return;
  }
  
  const repoInfo = getRepositoryInfo(config);
  
  if (repoInfo.ok) {
    SpreadsheetApp.getUi().alert(`
✅ GitHub 接続成功！

リポジトリ: ${repoInfo.name}
プライベート: ${repoInfo.isPrivate ? 'はい' : 'いいえ'}
URL: ${repoInfo.url}
    `.trim());
  } else {
    SpreadsheetApp.getUi().alert(`
❌ GitHub 接続失敗

エラー: ${repoInfo.error}

確認事項：
- GITHUB_TOKEN が正しく設定されているか？
- GitHub リポジトリ が存在するか？
- トークンに適切な権限があるか？
    `.trim());
  }
}
