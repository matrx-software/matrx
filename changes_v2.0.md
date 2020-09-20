- in loop.js, changed lv_update_url to work with GET parameters
- in loop.js change lv_update_url to have GET parameters
- add offsets as a variable to gen_grid
- removed API calls:
```
@app.route('/get_messages/<tick>/<agent_id>', methods=['GET'])
@app.route('/get_messages/<tick>', methods=['GET', 'POST'])
@app.route('/get_messages/<agent_id>', methods=['GET', 'POST'])
@app.route('/get_latest_messages', methods=['GET', 'POST'])
@app.route('/get_latest_messages/<agent_id>', methods=['GET', 'POST'])
def deprecated_get_messages(agent_id):
    #TODO: deprecated
    return jsonify(True)
```
- changes in toolbar.js, all related to the chat:
    - `populate_new_chat_dropdown`
    - `open_chatroom`
    - `add_chatroom`
    - `add_message`
    - `send_message`
    - global variables in file

- `gen_grid.js`:
    - Removed `process_messages` and `process_message` (have been moved to toolbar.js).
    - Removed `messages` var from gen_grid.js
    - Changed `process_messages(new_messages)` to `process_messages(new_messages, accessible_chatrooms)`



Features:
- An overhaul of the chat functionality (updated MATRX visualizer) and some backend changes in the `message_manager` and MATRX API calls for fetching messages to make fetching messages more robust.
For upgrading your custom MATRX v1.x.x frontend to MATRX v2.0.0, see this tutorial: ...
The changes more in depth:
    - Fetching MATRX messages via the API has been changed to work with `chat_offsets` instead of ticks, as ticks often resulted in difficulties with the default MATRX visualizer that occasionaly skipped ticks resulting in messages being missed.
    Now by requesting the latest API messages from the frontend with the latest message index of each message, the MATRX API server will send all messages which had been missed or are new from that message onwards. Thus never missing a message.  
    https://github.com/matrx-software/matrx/issues/222
    - Simplified the API. There is now 1 dedicated API call for fetching messages from MATRX:`/get_messages`. This API call accepts the URL parameter `agent_id` and `chat_offsets`. See above..
    - The API call `/get_latest_state_and_messages` has been updated to `message_manager` changes. The API call now accepts the `agent_id` and `chat_offsets` URL parameters.
    - In the default MATRX visualizer have the `toolbar.js` and `loop.js` files been upgraded to work with the changes in the API changes for fetching MATRX messages and use the `chat_offsets` for robust message fetching.
- God agents can now see all other chats (but not respond)



Questions:
- should an agent be able to start a chat with any single agent? Now: yes 
