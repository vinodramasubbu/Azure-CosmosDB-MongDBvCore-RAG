import React, { useState } from 'react';
import './Chat.css';
import uuid from 'react-uuid';
import logo from './copilot.jpg';


const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [assistant_message, setAssistant_message] = useState('');
  const [inputValue, setInputValue] = useState('');
  //const [session_id, setSession_id] = useState(uuid());
  const [session_id] = useState(uuid());


  const sendMessage = async () => {
  console.log(JSON.stringify({ prompt: inputValue, session_id: session_id }));
  
  const response = await fetch('/api/VectorSearch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ prompt: inputValue, session_id: session_id })
    });

    const data = await response.json()
    const assistout = JSON.parse(JSON.stringify(data));
    console.log(assistout.output);
    setMessages([...messages, { text: inputValue, isUser: true }, { text: assistout.output, isUser: false }]);
    setAssistant_message([...assistant_message, { text: data, isUser: false }, { text: data.message, isUser: false }]);

    setInputValue('');
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="chat">
    <img src={logo} alt="Logo" width="500" height="100"/>
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} style={{ textAlign: message.isUser ? 'right' : 'left' }}>
            {message.text}
          </div>
        ))}
      </div>
      </div>
      <div className="chat-input">
        <input type="text" value={inputValue} onChange={(event) => setInputValue(event.target.value)} onKeyDown={handleKeyDown} />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chat;