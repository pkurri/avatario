"""
Web Widget Embed System
Generates embeddable chat widget for websites
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json
import html

@dataclass
class WidgetConfig:
    widget_id: str
    business_id: str
    business_name: str
    persona_id: str = "anya"
    primary_color: str = "#3B82F6"
    position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left
    greeting_message: str = "Hi there! How can I help you today?"
    auto_open: bool = False
    auto_open_delay: int = 5  # seconds
    show_avatar: bool = True
    allow_voice: bool = True
    allow_file_upload: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    custom_css: Optional[str] = None
    privacy_message: str = "Messages are processed by AI"

class WebWidgetGenerator:
    def __init__(self):
        self.widgets: Dict[str, WidgetConfig] = {}
        self.default_config = WidgetConfig(
            widget_id="default",
            business_id="default",
            business_name="AI Assistant"
        )
    
    def create_widget(self, config: WidgetConfig) -> str:
        """Create a new widget configuration"""
        self.widgets[config.widget_id] = config
        return config.widget_id
    
    def get_widget(self, widget_id: str) -> Optional[WidgetConfig]:
        """Get widget configuration"""
        return self.widgets.get(widget_id)
    
    def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> bool:
        """Update widget configuration"""
        widget = self.widgets.get(widget_id)
        if not widget:
            return False
        
        for key, value in updates.items():
            if hasattr(widget, key):
                setattr(widget, key, value)
        
        return True
    
    def delete_widget(self, widget_id: str) -> bool:
        """Delete a widget"""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            return True
        return False
    
    def generate_embed_code(self, widget_id: str, api_base_url: str = "https://api.avatario.com") -> str:
        """Generate JavaScript embed code for a widget"""
        widget = self.get_widget(widget_id)
        if not widget:
            return ""
        
        config_json = json.dumps({
            "widgetId": widget.widget_id,
            "businessId": widget.business_id,
            "businessName": widget.business_name,
            "personaId": widget.persona_id,
            "primaryColor": widget.primary_color,
            "position": widget.position,
            "greetingMessage": widget.greeting_message,
            "autoOpen": widget.auto_open,
            "autoOpenDelay": widget.auto_open_delay,
            "showAvatar": widget.show_avatar,
            "allowVoice": widget.allow_voice,
            "allowFileUpload": widget.allow_file_upload,
            "privacyMessage": widget.privacy_message,
            "apiBaseUrl": api_base_url
        })
        
        embed_code = f"""<!-- Avatario AI Chat Widget -->
<script>
(function() {{
    // Widget Configuration
    window.AvatarConfig = {config_json};
    
    // Load Widget Script
    var script = document.createElement('script');
    script.src = '{api_base_url}/widget/v1/avatar-widget.js';
    script.async = true;
    script.onload = function() {{
        console.log('Avatar widget loaded successfully');
    }};
    script.onerror = function() {{
        console.error('Failed to load Avatar widget');
    }};
    document.head.appendChild(script);
}})();
</script>
<!-- End Avatario AI Chat Widget -->"""
        
        return embed_code
    
    def generate_iframe_embed(self, widget_id: str, api_base_url: str = "https://api.avatario.com") -> str:
        """Generate iframe embed code for a widget"""
        widget = self.get_widget(widget_id)
        if not widget:
            return ""
        
        iframe_src = f"{api_base_url}/widget/v1/chat?widget_id={widget_id}&business_id={widget.business_id}"
        
        iframe_code = f"""<!-- Avatario AI Chat Widget (Iframe) -->
<iframe
    src="{iframe_src}"
    width="400"
    height="600"
    frameborder="0"
    style="position: fixed; {self._get_position_css(widget.position)}; z-index: 9999; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"
    title="AI Chat Assistant"
></iframe>
<!-- End Avatario AI Chat Widget -->"""
        
        return iframe_code
    
    def _get_position_css(self, position: str) -> str:
        """Get CSS for widget position"""
        positions = {
            "bottom-right": "bottom: 20px; right: 20px",
            "bottom-left": "bottom: 20px; left: 20px",
            "top-right": "top: 20px; right: 20px",
            "top-left": "top: 20px; left: 20px"
        }
        return positions.get(position, positions["bottom-right"])
    
    def generate_widget_script(self) -> str:
        """Generate the main widget JavaScript file content"""
        script = """
// Avatario AI Chat Widget v1.0
(function(window, document) {
    'use strict';
    
    class AvatarWidget {
        constructor(config) {
            this.config = config;
            this.isOpen = false;
            this.isTyping = false;
            this.messages = [];
            this.websocket = null;
            this.init();
        }
        
        init() {
            this.createStyles();
            this.createDOM();
            this.attachEvents();
            
            if (this.config.autoOpen) {
                setTimeout(() => this.open(), this.config.autoOpenDelay * 1000);
            }
        }
        
        createStyles() {
            const styles = `
                .avatar-widget-container {
                    position: fixed;
                    ${this.getPositionCSS()}
                    z-index: 9999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .avatar-widget-button {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: ${this.config.primaryColor};
                    color: white;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.2s;
                }
                
                .avatar-widget-button:hover {
                    transform: scale(1.05);
                }
                
                .avatar-widget-chat {
                    position: absolute;
                    bottom: 70px;
                    ${this.config.position.includes('right') ? 'right' : 'left'}: 0;
                    width: 380px;
                    height: 500px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                .avatar-widget-chat.open {
                    display: flex;
                }
                
                .avatar-widget-header {
                    background: ${this.config.primaryColor};
                    color: white;
                    padding: 16px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .avatar-widget-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .avatar-widget-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                
                .avatar-widget-message {
                    max-width: 80%;
                    padding: 12px;
                    border-radius: 12px;
                    word-wrap: break-word;
                }
                
                .avatar-widget-message.user {
                    align-self: flex-end;
                    background: ${this.config.primaryColor};
                    color: white;
                }
                
                .avatar-widget-message.ai {
                    align-self: flex-start;
                    background: #f3f4f6;
                    color: #1f2937;
                }
                
                .avatar-widget-input-area {
                    padding: 12px;
                    border-top: 1px solid #e5e7eb;
                    display: flex;
                    gap: 8px;
                }
                
                .avatar-widget-input {
                    flex: 1;
                    padding: 10px 14px;
                    border: 1px solid #e5e7eb;
                    border-radius: 20px;
                    outline: none;
                }
                
                .avatar-widget-send {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: ${this.config.primaryColor};
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .avatar-widget-typing {
                    display: flex;
                    gap: 4px;
                    padding: 12px;
                    align-self: flex-start;
                }
                
                .avatar-widget-typing-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #9ca3af;
                    animation: typing 1.4s infinite;
                }
                
                @keyframes typing {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-10px); }
                }
            `;
            
            const styleSheet = document.createElement('style');
            styleSheet.textContent = styles;
            document.head.appendChild(styleSheet);
        }
        
        createDOM() {
            const container = document.createElement('div');
            container.className = 'avatar-widget-container';
            
            container.innerHTML = `
                <div class="avatar-widget-chat" id="avatar-chat">
                    <div class="avatar-widget-header">
                        <div class="avatar-widget-avatar">AI</div>
                        <div>
                            <div style="font-weight: 600;">${this.escapeHtml(this.config.businessName)}</div>
                            <div style="font-size: 12px; opacity: 0.9;">Online</div>
                        </div>
                    </div>
                    <div class="avatar-widget-messages" id="avatar-messages"></div>
                    <div class="avatar-widget-input-area">
                        <input type="text" class="avatar-widget-input" id="avatar-input" 
                               placeholder="Type your message..." />
                        <button class="avatar-widget-send" id="avatar-send">→</button>
                    </div>
                </div>
                <button class="avatar-widget-button" id="avatar-button">
                    💬
                </button>
            `;
            
            document.body.appendChild(container);
            
            // Cache DOM elements
            this.button = document.getElementById('avatar-button');
            this.chat = document.getElementById('avatar-chat');
            this.messagesContainer = document.getElementById('avatar-messages');
            this.input = document.getElementById('avatar-input');
            this.sendButton = document.getElementById('avatar-send');
            
            // Add greeting message
            this.addMessage(this.config.greetingMessage, 'ai');
        }
        
        attachEvents() {
            this.button.addEventListener('click', () => this.toggle());
            
            this.sendButton.addEventListener('click', () => this.sendMessage());
            
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
        
        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }
        
        open() {
            this.isOpen = true;
            this.chat.classList.add('open');
            this.input.focus();
        }
        
        close() {
            this.isOpen = false;
            this.chat.classList.remove('open');
        }
        
        sendMessage() {
            const text = this.input.value.trim();
            if (!text) return;
            
            this.addMessage(text, 'user');
            this.input.value = '';
            
            this.showTyping();
            
            // Send to backend
            this.sendToAI(text);
        }
        
        async sendToAI(text) {
            try {
                const response = await fetch(`${this.config.apiBaseUrl}/widget/message`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        widget_id: this.config.widgetId,
                        business_id: this.config.businessId,
                        message: text,
                        persona_id: this.config.personaId
                    })
                });
                
                const data = await response.json();
                this.hideTyping();
                this.addMessage(data.response, 'ai');
                
            } catch (error) {
                this.hideTyping();
                this.addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
            }
        }
        
        addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `avatar-widget-message ${sender}`;
            messageDiv.textContent = text;
            this.messagesContainer.appendChild(messageDiv);
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
        
        showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'avatar-widget-typing';
            typingDiv.id = 'avatar-typing';
            typingDiv.innerHTML = `
                <div class="avatar-widget-typing-dot" style="animation-delay: 0s;"></div>
                <div class="avatar-widget-typing-dot" style="animation-delay: 0.2s;"></div>
                <div class="avatar-widget-typing-dot" style="animation-delay: 0.4s;"></div>
            `;
            this.messagesContainer.appendChild(typingDiv);
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
        
        hideTyping() {
            const typing = document.getElementById('avatar-typing');
            if (typing) typing.remove();
        }
        
        getPositionCSS() {
            const positions = {
                'bottom-right': 'bottom: 20px; right: 20px;',
                'bottom-left': 'bottom: 20px; left: 20px;',
                'top-right': 'top: 20px; right: 20px;',
                'top-left': 'top: 20px; left: 20px;'
            };
            return positions[this.config.position] || positions['bottom-right'];
        }
        
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new AvatarWidget(window.AvatarConfig);
        });
    } else {
        new AvatarWidget(window.AvatarConfig);
    }
    
})(window, document);
"""
        return script


# Global widget generator instance
widget_generator = WebWidgetGenerator()


def get_widget_generator() -> WebWidgetGenerator:
    """Get the global widget generator instance"""
    return widget_generator


# Example usage
if __name__ == "__main__":
    # Create a widget
    config = WidgetConfig(
        widget_id="demo_widget_001",
        business_id="law_firm_001",
        business_name="Legal Solutions LLC",
        persona_id="lawyer",
        primary_color="#4F46E5",
        position="bottom-right",
        greeting_message="Hello! I'm here to help with your legal questions. What can I assist you with?",
        auto_open=True,
        auto_open_delay=3
    )
    
    generator = get_widget_generator()
    widget_id = generator.create_widget(config)
    
    # Generate embed code
    embed_code = generator.generate_embed_code(widget_id, "https://api.avatario.com")
    
    print("Generated Embed Code:")
    print("=" * 60)
    print(embed_code)
    print("=" * 60)
    print("\nTo use this widget:")
    print("1. Copy the embed code above")
    print("2. Paste it into your website's HTML, just before </body>")
    print("3. The widget will automatically load and appear on your site")
