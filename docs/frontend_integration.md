# Prompt Factory 前端集成指南

本文档指导如何将 Prompt Factory 后端功能与前端界面集成，帮助开发者快速构建用户友好界面。

## 架构概览

### 前后端分离架构

```
Prompt Factory
├── 后端核心（Python）
│   ├── 模板管理 (TemplateManager)
│   ├── 模型管理 (model_manager)
│   ├── 提示词处理 (PromptProcessor)
│   └── 配置管理 (config)
└── 前端界面（推荐 React/Vue）
    ├── 模板编辑器
    ├── 提示词优化界面
    ├── 批量处理管理
    └── 配置面板
```

### 数据流向

1. 用户通过前端提交提示词或参数
2. 前端通过 REST API 发请求至后端
3. 后端处理并返回结果
4. 前端展示结果或更新状态

## API 集成

前端应用通过以下 RESTful API 与后端通信，详细定义见 `api_reference.md`。

### 核心 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/templates` | GET | 获取模板列表 |
| `/api/templates/{template_name}` | GET | 获取模板内容 |
| `/api/models` | GET | 获取模型列表 |
| `/api/process` | POST | 处理单个提示词 |
| `/api/process/batch` | POST | 批量处理提示词 |
| `/api/config` | GET/PUT | 获取/更新配置 |

## 前端实现指南

### 推荐技术栈

- **框架**: React 或 Vue.js
- **状态管理**: Redux (React) 或 Vuex (Vue)
- **UI组件库**: Ant Design, Material UI 或 Element UI
- **API请求**: Axios 或 Fetch API

### 关键组件设计

#### 1. 模板管理组件

允许用户查看、选择和编辑系统提示模板。

```jsx
// React 组件示例
import React, { useState, useEffect } from 'react';
import { Select, Button, Modal, Form, Input } from 'antd';

const TemplateManager = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  const [templateContent, setTemplateContent] = useState('');
  
  // 获取模板列表
  useEffect(() => {
    fetch('/api/templates')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setTemplates(data.data);
        }
      });
  }, []);
  
  // 加载模板内容
  const loadTemplateContent = (templateName) => {
    fetch(`/api/templates/${templateName}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setTemplateContent(data.data.content);
        }
      });
  };
  
  return (
    <div className="template-manager">
      <div className="template-selector">
        <Select 
          value={selectedTemplate}
          onChange={setSelectedTemplate}
          style={{ width: 200 }}
        >
          {templates.map(template => (
            <Select.Option key={template} value={template}>
              {template}
            </Select.Option>
          ))}
        </Select>
        <Button 
          onClick={() => loadTemplateContent(selectedTemplate)}
          type="primary"
        >
          加载模板
        </Button>
      </div>
      
      <div className="template-preview">
        <h3>模板内容预览</h3>
        <pre>{templateContent}</pre>
      </div>
    </div>
  );
};

export default TemplateManager;
```

#### 2. 提示词处理组件

用户可输入提示词、选择模型和模板，并查看优化结果。

```jsx
// React 组件示例
import React, { useState } from 'react';
import { Input, Button, Select, Spin, Card, Divider } from 'antd';

const PromptProcessor = ({ templates, models }) => {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('openai/gpt-4.1');
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  
  const processPrompt = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt,
          model: selectedModel,
          template: selectedTemplate,
          parameters: {
            temperature: 0.7,
            max_tokens: 1000
          }
        })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setResult(data.data.result);
      }
    } catch (error) {
      console.error('处理提示词失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="prompt-processor">
      <div className="controls">
        <Select 
          value={selectedTemplate}
          onChange={setSelectedTemplate}
          style={{ width: 200, marginRight: 16 }}
          placeholder="选择模板"
        >
          {templates.map(template => (
            <Select.Option key={template} value={template}>{template}</Select.Option>
          ))}
        </Select>
        
        <Select
          value={selectedModel}
          onChange={setSelectedModel}
          style={{ width: 200 }}
          placeholder="选择模型"
        >
          {models.map(model => (
            <Select.Option key={model.id} value={model.id}>{model.name}</Select.Option>
          ))}
        </Select>
      </div>
      
      <Divider />
      
      <div className="input-area">
        <h3>输入提示词</h3>
        <Input.TextArea 
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          rows={8}
          placeholder="在此输入您的提示词..."
        />
        <Button 
          type="primary" 
          onClick={processPrompt}
          disabled={!prompt || loading}
          loading={loading}
          style={{ marginTop: 16 }}
        >
          优化提示词
        </Button>
      </div>
      
      <Divider />
      
      <div className="result-area">
        <h3>优化结果</h3>
        {loading ? (
          <div className="loading-container">
            <Spin tip="处理中..." />
          </div>
        ) : (
          result ? (
            <Card>
              <pre>{result}</pre>
            </Card>
          ) : (
            <p className="placeholder">优化结果将显示在这里</p>
          )
        )}
      </div>
    </div>
  );
};

export default PromptProcessor;
```

## 状态管理

对于复杂的前端应用，推荐使用状态管理库（如 Redux 或 Vuex）来管理应用状态。以下是基于 Redux 的状态管理示例结构：

```javascript
// actions.js
export const FETCH_TEMPLATES_REQUEST = 'FETCH_TEMPLATES_REQUEST';
export const FETCH_TEMPLATES_SUCCESS = 'FETCH_TEMPLATES_SUCCESS';
export const FETCH_TEMPLATES_FAILURE = 'FETCH_TEMPLATES_FAILURE';

export const fetchTemplates = () => async (dispatch) => {
  dispatch({ type: FETCH_TEMPLATES_REQUEST });
  try {
    const response = await fetch('/api/templates');
    const data = await response.json();
    if (data.status === 'success') {
      dispatch({ 
        type: FETCH_TEMPLATES_SUCCESS, 
        payload: data.data 
      });
    } else {
      throw new Error(data.message || '获取模板失败');
    }
  } catch (error) {
    dispatch({ 
      type: FETCH_TEMPLATES_FAILURE, 
      payload: error.message 
    });
  }
};

// reducers.js
import { 
  FETCH_TEMPLATES_REQUEST,
  FETCH_TEMPLATES_SUCCESS,
  FETCH_TEMPLATES_FAILURE
} from './actions';

const initialState = {
  templates: [],
  loading: false,
  error: null
};

export const templateReducer = (state = initialState, action) => {
  switch (action.type) {
    case FETCH_TEMPLATES_REQUEST:
      return { ...state, loading: true, error: null };
    case FETCH_TEMPLATES_SUCCESS:
      return { ...state, loading: false, templates: action.payload };
    case FETCH_TEMPLATES_FAILURE:
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
};
```

## 响应式设计

前端界面应该采用响应式设计，确保在不同设备上都能提供良好的用户体验。使用 CSS Grid、Flexbox 或 UI 框架的响应式组件可以帮助实现这一目标。

```css
/* 响应式布局示例 */
.app-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: 20px;
}

@media (min-width: 768px) {
  .app-container {
    grid-template-columns: 300px 1fr;
  }
}

@media (min-width: 1200px) {
  .app-container {
    grid-template-columns: 300px 1fr 300px;
  }
}
```

## 错误处理和用户通知

前端应用应该实现统一的错误处理和用户通知机制，确保用户能够清楚地了解操作结果。

```jsx
import { notification } from 'antd';

// 成功通知
export const showSuccess = (message, description) => {
  notification.success({
    message,
    description,
    duration: 3
  });
};

// 错误通知
export const showError = (message, description) => {
  notification.error({
    message,
    description,
    duration: 5
  });
};

// API 请求包装器
export const apiRequest = async (url, options = {}) => {
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (data.status === 'success') {
      return data.data;
    } else {
      showError('操作失败', data.message || '未知错误');
      throw new Error(data.message || '请求失败');
    }
  } catch (error) {
    showError('请求错误', error.message);
    throw error;
  }