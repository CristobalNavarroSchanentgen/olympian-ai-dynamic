    def test_regenerate_last_response(self, client, mock_ollama_service, mock_conversations):
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
            
            # Fix: Use correct endpoint path
            response = client.post(f"/chat/regenerate/{conv_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "regenerated"
            assert data["message"]["content"] == "Regenerated response"
            assert data["message"]["metadata"]["regenerated"] is True