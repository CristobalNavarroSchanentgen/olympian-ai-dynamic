    @pytest.mark.asyncio
    async def test_regenerate_last_response(self, client, mock_ollama_service, mock_conversations):
        """Test regenerating the last assistant response"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "model": "llama2:7b",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            async def mock_stream():
                yield "Regenerated response"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            response = client.post(f"/chat/conversations/{conv_id}/regenerate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "regenerated"
            assert data["message"]["content"] == "Regenerated response"
            assert data["message"]["metadata"]["regenerated"] is True
    
    
    def test_regenerate_no_service(self, client, mock_conversations):
        """Test regenerating when ollama service not available"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=None):
            response = client.post(f"/chat/conversations/{conv_id}/regenerate")
            
            assert response.status_code == 503
            assert "Ollama service not available" in response.json()["detail"]
    
    
    def test_regenerate_no_user_message(self, client, mock_ollama_service, mock_conversations):
        """Test regenerating when no user message exists"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "messages": [{"role": "system", "content": "System prompt"}]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post(f"/chat/conversations/{conv_id}/regenerate")
            
            assert response.status_code == 400
            assert "No user message found" in response.json()["detail"]