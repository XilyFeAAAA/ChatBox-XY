好的，我们来具体探讨如何让这个大模型上下文管理系统与你的 COC (Call of Cthulhu) 跑团插件进行交互。

**核心目标：**

1.  **AI作为KP（守秘人）：** LLM 需要扮演 KP 的角色，理解玩家行动，推进剧情，描述场景，扮演NPC，并根据规则进行判定。
2.  **上下文管理：** 保持跑团的长期对话历史，并在 token 限制内有效传递给 LLM。
3.  **工具调用 (Tool Calling/Function Calling)：** 允许 AI (KP) 调用外部工具，例如：
    *   **掷骰子 (Dice Roller):** `d100`, `d6`, `奖励骰`, `惩罚骰` 等。
    *   **规则查询 (Rule Lookup):** （可选，较复杂）查询特定技能检定、战斗规则等。
    *   **角色状态更新 (Character Sheet Updater):** 更新玩家的 HP, SAN, 技能点等。（更高级，可能需要外部数据库）
    *   **笔记记录 (Note Taker):** AI 主动记录关键线索、NPC 信息等。

**交互流程与系统设计调整：**

让我们回顾一下系统组件，并思考 COC 插件如何融入：

```
+-------------------------+
|    Chatbox Application  | (微信机器人)
+-------------------------+
          |
          v
+-------------------------+
|  Plugin Manager         | -- Knows current plugin is COC
|  (海龟汤, COC)          |
+-------------------------+
          |
          v
+-------------------------------------+     <-----------------+
| Context Management System (CMS)     |                       | (LLM API)
+-------------------------------------+                       |
    |  |                                |                       |
    |  +-- Prompt Engine              |                       |
    |  |   (Uses COC_KP_PROMPT)       |                       |
    |  +-- History Store              | --- (DB/Cache)        |
    |  |   (Stores player actions,    |                       |
    |  |    KP narrations, tool calls)|                       |
    |  +-- Summarization Engine       | --- (调用LLM) ----> +-----------+
    |  |   (COC-specific summary hint)|                       | LLM Service|
    |  +-- Tokenizer                  |                       +-----------+
    |  +-- Strategy Engine            |                       |
    |  |                                |                       |
    |  +-- Tool Handler (New Component)| --- (Calls COC Plugin Functions)
    |                                  |
    +-- Configurable Parameters        |
          (COC specific settings)      |
                                       |
                                       v
+-------------------------------------+
| COC Plugin                          |
| - define_coc_tools()                |
| - roll_dice(type, bonus, penalty)   |
| - update_character_sheet(...)       |
| - get_coc_world_state_summary()     |
+-------------------------------------+
```

**1. COC 插件 (`coc_plugin.py`)**

这个插件将包含 COC 跑团的核心逻辑和与 LLM 交互所需的特定功能。

```python
# coc_plugin.py
import random
import json

class COCPlugin:
    def __init__(self):
        # 可以在这里初始化角色卡、当前场景信息等
        self.character_sheets = {} # e.g., {"player_id": {"hp": 10, "san": 50, ...}}
        self.current_scene_notes = "起始场景：你们在一间昏暗的旧书店里..."
        print("COC Plugin Initialized.")

    def get_kp_system_prompt(self) -> str:
        from config import COC_KP_PROMPT # Import here to avoid circularity if config imports this
        # 可以动态加入一些当前游戏状态的简要提示
        # prompt = COC_KP_PROMPT + f"\n\n当前关键信息提示：{self.get_coc_world_state_summary(short=True)}"
        return COC_KP_PROMPT

    def define_coc_tools(self) -> list:
        """
        定义供 LLM 调用的工具列表 (OpenAI Function Calling format)。
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "roll_dice",
                    "description": "掷一个或多个COC规则的骰子。例如 d100, 2d6, 奖励骰, 惩罚骰。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dice_type": {
                                "type": "string",
                                "description": "骰子类型，如 'd100', 'd6', 'd10', 'd4', 'd8', 'd20'等。"
                            },
                            "num_dice": {
                                "type": "integer",
                                "description": "要掷的骰子数量，默认为1。",
                                "default": 1
                            },
                            "bonus_dice": {
                                "type": "integer",
                                "description": "奖励骰的数量 (0, 1, or 2)。奖励骰会多掷这些数量的十位骰，并取结果中较好的一个十位。",
                                "default": 0
                            },
                            "penalty_dice": {
                                "type": "integer",
                                "description": "惩罚骰的数量 (0, 1, or 2)。惩罚骰会多掷这些数量的十位骰，并取结果中较差的一个十位。",
                                "default": 0
                            },
                            "reason": {
                                "type": "string",
                                "description": "掷骰的原因或对应的技能/属性，例如 '侦查检定', '图书馆使用', '伤害骰'。"
                            }
                        },
                        "required": ["dice_type", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_character_skill_value",
                    "description": "查询指定玩家的某个技能或属性的当前值。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "player_name": {"type": "string", "description": "玩家的名字或代号。"},
                            "skill_or_attribute": {"type": "string", "description": "要查询的技能或属性名称，例如 '侦查', '图书馆使用', '力量', '理智'。"}
                        },
                        "required": ["player_name", "skill_or_attribute"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_player_stat",
                    "description": "更新玩家的特定属性，如HP或SAN值。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "player_name": {"type": "string", "description": "玩家的名字或代号。"},
                            "stat_name": {"type": "string", "description": "要更新的属性名，如 'HP', 'SAN'。"},
                            "change_value": {"type": "integer", "description": "改变的值，正数表示增加，负数表示减少。"},
                            "reason": {"type": "string", "description": "属性改变的原因。"}
                        },
                        "required": ["player_name", "stat_name", "change_value", "reason"]
                    }
                }
            }
            # 可以添加更多工具，如:
            # - get_scene_description(scene_name)
            # - get_npc_info(npc_name)
            # - record_clue(clue_text)
        ]
        return tools

    # --- Tool Implementations ---
    def roll_dice(self, dice_type: str, num_dice: int = 1, bonus_dice: int = 0, penalty_dice: int = 0, reason: str = "") -> str:
        results = []
        details = []

        if dice_type.lower() == 'd100':
            if bonus_dice > 0 and penalty_dice > 0:
                return json.dumps({"error": "不能同时有奖励骰和惩罚骰。"}) # 返回 JSON 字符串
            
            tens_rolls = [random.randint(0, 9) * 10 for _ in range(1 + bonus_dice + penalty_dice)]
            units_roll = random.randint(0, 9) # 0代表100中的0，除非十位也是0（此时为100）
            
            if bonus_dice > 0:
                chosen_tens = min(tens_rolls) # 取好的（小的）
                details.append(f"奖励骰十位: {tens_rolls}, 选取: {chosen_tens}")
            elif penalty_dice > 0:
                chosen_tens = max(tens_rolls) # 取差的（大的）
                details.append(f"惩罚骰十位: {tens_rolls}, 选取: {chosen_tens}")
            else:
                chosen_tens = tens_rolls[0]
                details.append(f"十位骰: {chosen_tens}")

            details.append(f"个位骰: {units_roll}")
            
            final_result = chosen_tens + units_roll
            if final_result == 0: # 00 + 0 应该算作 100
                final_result = 100
            results.append(final_result)

        else: # 简单多面骰
            try:
                sides = int(dice_type[1:])
                for _ in range(num_dice):
                    results.append(random.randint(1, sides))
            except ValueError:
                return json.dumps({"error": f"不支持的骰子类型: {dice_type}"})

        total = sum(results)
        output = {
            "reason": reason,
            "dice_type": dice_type,
            "num_dice": num_dice,
            "bonus_dice": bonus_dice,
            "penalty_dice": penalty_dice,
            "rolls": results,
            "total": total if len(results) > 1 and dice_type.lower() != 'd100' else None, # d100通常不看total
            "result_d100": results[0] if dice_type.lower() == 'd100' else None,
            "details": ", ".join(details) if details else None
        }
        return json.dumps(output) # LLM 需要 JSON 字符串作为工具的返回

    def get_character_skill_value(self, player_name: str, skill_or_attribute: str) -> str:
        # 这是一个简化的实现，实际中你可能需要从更复杂的数据结构中读取
        player_sheet = self.character_sheets.get(player_name.lower(), {})
        value = player_sheet.get(skill_or_attribute.lower(), "未知或未设置") # 例如: {"侦查": 60, "san": 55}
        if isinstance(value, (int, float)):
             return json.dumps({"player": player_name, "skill": skill_or_attribute, "value": value})
        else:
             # 如果技能不存在，可以提示KP
             return json.dumps({"player": player_name, "skill": skill_or_attribute, "value": None, "note": f"技能 '{skill_or_attribute}' 在角色卡中未找到。KP请注意。"})


    def update_player_stat(self, player_name: str, stat_name: str, change_value: int, reason: str) -> str:
        player_sheet = self.character_sheets.setdefault(player_name.lower(), {})
        current_value = player_sheet.get(stat_name.lower(), 0) # 假设默认是0
        new_value = current_value + change_value
        player_sheet[stat_name.lower()] = new_value
        
        # 可以在这里添加SAN值过低等的特殊处理逻辑
        if stat_name.lower() == 'san' and new_value <= 0:
            # ... 永久疯狂逻辑 ...
            pass

        return json.dumps({
            "player": player_name,
            "stat": stat_name,
            "old_value": current_value,
            "change": change_value,
            "new_value": new_value,
            "reason": reason,
            "status": "success"
        })


    def get_coc_world_state_summary(self, short: bool = False) -> str:
        """
        (供 ContextBuilder 使用) 提供一个关于当前跑团状态的简要文本。
        这可以被注入到上下文的System Prompt或者作为一条特殊的 'system' or 'assistant' 消息。
        """
        # 示例实现，你需要根据你的游戏状态来填充
        summary_parts = []
        summary_parts.append(f"当前场景: {self.current_scene_notes[:100]}{'...' if len(self.current_scene_notes) > 100 else ''}")
        
        if not short:
            for player, sheet in self.character_sheets.items():
                hp = sheet.get('hp', 'N/A')
                san = sheet.get('san', 'N/A')
                summary_parts.append(f"玩家 {player.capitalize()}: HP {hp}, SAN {san}")
        
        # 还可以包括关键NPC，未解之谜等
        return "\n".join(summary_parts)

    def get_coc_summary_instruction_hint(self) -> str:
        """ (供 Summarizer 使用) """
        return (
            "请总结以上COC跑团记录，重点包括：\n"
            "1. 玩家的重要行动和决策。\n"
            "2. KP描述的关键场景变化和NPC互动。\n"
            "3. 任何重要的检定结果及其影响。\n"
            "4. 新发现的线索或未解的谜题。\n"
            "摘要应该能让KP快速回忆起剧情进展和当前状态。"
        )

# 示例：初始化一个玩家，实际应用中可能通过指令或配置文件
# coc_game = COCPlugin()
# coc_game.character_sheets["alice"] = {"hp": 12, "san": 60, "侦查": 70, "图书馆使用": 50}
# coc_game.character_sheets["bob"] = {"hp": 10, "san": 55, "潜行": 60, "恐吓": 40}
```

**2. `ToolHandler` (新组件或集成到 `LLMClient` / `ChatApplication`)**

这个组件负责：

*   接收来自 LLM 的 `tool_calls`。
*   根据 `function.name` 调用 `COCPlugin` 中相应的函数。
*   将函数的返回值（通常是JSON字符串）封装成 `tool` 角色的消息。

```python
# Part of llm_client.py or a new tool_handler.py
# Let's assume it's part of ChatApplication for now in main_direct_openai.py

# ... (in ChatApplication or a dedicated handler)
# self.coc_plugin = COCPlugin() # If COC mode is active

def execute_tool_call(self, tool_call: dict) -> dict: # Returns a message for history
    """
    Executes a single tool call from the LLM and returns a message for history.
    """
    tool_id = tool_call['id']
    func_name = tool_call['function']['name']
    try:
        func_args_json = tool_call['function']['arguments']
        func_args = json.loads(func_args_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding arguments for {func_name}: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": func_name,
            "content": json.dumps({"error": f"Invalid JSON arguments: {func_args_json}"})
        }

    print(f"Executing tool: {func_name} with args: {func_args}")

    if not hasattr(self.coc_plugin, func_name):
        print(f"Error: Tool '{func_name}' not found in COCPlugin.")
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": func_name,
            "content": json.dumps({"error": f"Tool function '{func_name}' not implemented."})
        }

    try:
        callable_func = getattr(self.coc_plugin, func_name)
        # Use inspect to see if arguments match, or rely on LLM to provide correct ones
        # For simplicity, directly call with **func_args
        result_content_str = callable_func(**func_args) # Assumes function returns JSON string
        
        # Ensure the result is a string (as functions might return dicts before json.dumps)
        if not isinstance(result_content_str, str):
            print(f"Warning: Tool {func_name} did not return a string. Attempting to dump to JSON.")
            result_content_str = json.dumps(result_content_str)

    except TypeError as e: # Mismatched arguments
        print(f"Error calling tool {func_name} with args {func_args}: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": func_name,
            "content": json.dumps({"error": f"Argument mismatch for {func_name}: {e}"})
        }
    except Exception as e:
        print(f"Exception during tool {func_name} execution: {e}")
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": func_name,
            "content": json.dumps({"error": f"Internal error executing tool: {str(e)}"})
        }
    
    return {
        "role": "tool",
        "tool_call_id": tool_id,
        "name": func_name,
        "content": result_content_str
    }
```

**3. 修改 `LLMClient.get_chat_completion`**

需要让它能传递 `tools` 和 `tool_choice` 参数给 OpenAI API。

```python
# llm_client.py modifications

class LLMClient:
    # ... (init and other methods) ...

    def get_chat_completion(self,
                            messages: List[Dict[str, str]],
                            model: str = CHAT_MODEL,
                            max_tokens_response: int = 500,
                            temperature: float = 0.7,
                            system_prompt_override: Optional[str] = None,
                            tools: Optional[List[dict]] = None, # New parameter
                            tool_choice: Optional[Union[str, dict]] = "auto" # New parameter, "auto" is default
                           ) -> Tuple[Optional[str], Optional[List[dict]]]: # Return content AND tool_calls
        """
        Gets a chat completion from the OpenAI API.
        Can now handle tool calls.

        Returns:
            Tuple[Optional[str], Optional[List[dict]]]:
                - The content of the AI's response (if any).
                - A list of tool_calls requested by the AI (if any).
        """
        api_messages = messages.copy()
        if system_prompt_override:
            # ... (system prompt handling) ...

        request_params = {
            "model": model,
            "messages": api_messages,
            "max_tokens": max_tokens_response,
            "temperature": temperature
        }
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = tool_choice # e.g., "auto", {"type": "function", "function": {"name": "my_function"}}

        # print(f"\n--- Sending to LLM ({model}) with tools: {json.dumps(tools, indent=2) if tools else 'None'} ---")
        # ...

        try:
            response = self._request_with_retry(
                method_to_call=self.client.chat.completions.create,
                **request_params
            )
            if response and response.choices:
                choice = response.choices[0]
                message_from_llm = choice.message
                
                content = message_from_llm.content
                tool_calls = message_from_llm.tool_calls # This will be a list of ToolCall objects or None
                
                # Convert ToolCall objects to simple dicts for easier handling if needed,
                # or handle them directly. For now, let's assume they are serializable.
                # If tool_calls is not None, it's a list of objects like:
                # ToolCall(id='call_abc', function=Function(arguments='{"dice_type":"d100"}', name='roll_dice'), type='function')
                
                # Let's convert to list of dicts for consistency with what we expect in history
                parsed_tool_calls = None
                if tool_calls:
                    parsed_tool_calls = []
                    for tc in tool_calls:
                        parsed_tool_calls.append({
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        })

                return content, parsed_tool_calls # Return both
        except APIError as e:
            print(f"Error in get_chat_completion: {e}")
        return None, None
```

**4. 修改 `ChatApplication.run_chat` (在 `main_direct_openai.py`)**

这是主要的循环，需要处理工具调用。

```python
# main_direct_openai.py modifications

# ... (imports and ChatApplication init) ...
from coc_plugin import COCPlugin # Add this

class ChatApplication:
    def __init__(self, plugin_mode: Optional[str] = None):
        # ... (existing init) ...
        self.coc_plugin: Optional[COCPlugin] = None
        if self.plugin_mode and self.plugin_mode.lower() == "coc":
            self.coc_plugin = COCPlugin()
            # Example: Initialize some player data (in a real app, this would be loaded/managed)
            if self.coc_plugin:
                 self.coc_plugin.character_sheets["player1"] = {"name": "Investigator Alice", "hp": 12, "san": 60, "侦查": 70, "图书馆使用": 50}
                 self.coc_plugin.character_sheets["player2"] = {"name": "Investigator Bob", "hp": 10, "san": 55, "潜行": 60, "恐吓": 40}


    # ... (_calculate_max_response_tokens and execute_tool_call as defined before) ...
    def execute_tool_call(self, tool_call: dict) -> dict: # Ensure this method is part of ChatApplication
        # ... (implementation from step 2) ...
        # This method will use self.coc_plugin to call the actual tool functions
        pass


    def run_chat(self):
        print("\nStarting chat session...")
        # ... (initial print statements) ...
        
        is_coc_mode = self.plugin_mode and self.plugin_mode.lower() == "coc" and self.coc_plugin is not None

        while True:
            try:
                user_input = input("You: ")
            except (EOFError, KeyboardInterrupt): # Combined for brevity
                print("\nExiting chat.")
                break
            # ... (exit, clear, empty input handling) ...

            self.history_store.add_user_message(user_input)

            # Main loop for potential multi-turn tool usage
            MAX_TOOL_ITERATIONS = 5 # Prevent infinite loops
            current_tool_iterations = 0
            
            pending_messages_for_llm = [] # Start with user message for this turn

            while current_tool_iterations < MAX_TOOL_ITERATIONS:
                current_tool_iterations += 1

                print("System: Thinking...")
                
                # Prepare tools if in COC mode
                current_tools = self.coc_plugin.define_coc_tools() if is_coc_mode else None
                
                # Context building should happen fresh each time if we are in a tool loop,
                # or it can build upon the existing history.
                # For simplicity now, we build context from the full history each time.
                llm_context_messages, prompt_tokens = self.context_builder.get_and_manage_context(
                    plugin_system_prompt=self.system_prompt if self.plugin_mode else None
                )
                
                # Add any messages accumulated in this turn's tool loop (e.g. previous tool results)
                # The llm_context_messages ALREADY includes the full history from history_store.
                # What we need is to ensure that if the LLM called a tool, and we added the tool result
                # to history_store, the NEXT call to get_and_manage_context picks it up.

                print(f"System: Context ready ({prompt_tokens} tokens). Requesting response...")
                max_resp_tokens = self._calculate_max_response_tokens(prompt_tokens)

                ai_content, ai_tool_calls = self.llm_client.get_chat_completion(
                    messages=llm_context_messages, # This contains the full history
                    model=CHAT_MODEL,
                    max_tokens_response=max_resp_tokens,
                    tools=current_tools, # Pass defined tools
                    tool_choice="auto" if current_tools else None
                )

                # --- Process LLM Response ---
                assistant_message_parts = []
                if ai_content:
                    assistant_message_parts.append(ai_content)
                    # Add assistant's textual response to history immediately
                    # self.history_store.add_assistant_message(ai_content)
                    # print(f"AI: {ai_content}") # Print textual part

                if ai_tool_calls and is_coc_mode:
                    # LLM wants to call one or more tools
                    # Store the assistant's message that contains the tool_calls request
                    # The 'content' might be null or some text like "Okay, I'll roll the dice."
                    # The OpenAI API expects the assistant message that *requested* the tool call to be in history.
                    # The 'tool_calls' object itself isn't a message role but part of an assistant message.
                    
                    # We need to construct what the assistant's message *would look like* for history store
                    # This is a bit tricky, as our Message class doesn't directly store a `tool_calls` list.
                    # Option 1: Store a textual representation.
                    # Option 2: Enhance Message class. For now, let's go with textual for simplicity in history store Message.
                    # The raw `ai_tool_calls` (list of dicts) will be processed.

                    # Let's assume for now the assistant message for a tool call is just the textual part (if any)
                    # The critical part is that the *next* messages sent to the LLM include the `tool` role messages.
                    if ai_content: # If there was text alongside tool call
                        self.history_store.add_assistant_message(ai_content) # Add text part
                        print(f"AI: {ai_content}")
                    else: # If only tool_calls and no text, we might add a placeholder assistant message
                          # or rely on the tool messages themselves to continue context.
                          # For now, if no text, no separate assistant message added, only tool results.
                          # OpenAI's examples often show an assistant message *with* tool_calls.
                          # Let's simulate this by adding an assistant message that notes the tool calls
                          # (This is for our history store's view, not strictly how OpenAI API structures it internally for the call)
                        placeholder_content = f"[Assistant is attempting to use tools: {', '.join([tc['function']['name'] for tc in ai_tool_calls])}]"
                        self.history_store.add_assistant_message(placeholder_content)
                        # print(f"AI: {placeholder_content}") # Optional: print this placeholder


                    for tool_call_request in ai_tool_calls:
                        # This is the dict like {"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}
                        print(f"System: AI requests tool: {tool_call_request['function']['name']} with ID {tool_call_request['id']}")
                        
                        # Execute the tool
                        tool_response_message_dict = self.execute_tool_call(tool_call_request)
                        
                        # Add the tool's response (a message with role 'tool') to history
                        self.history_store.add_message(
                            role="tool",
                            content=tool_response_message_dict['content'], # This is the JSON string result
                            tool_call_id=tool_response_message_dict['tool_call_id'],
                            name=tool_response_message_dict['name']
                        )
                        print(f"Tool ({tool_response_message_dict['name']}): {tool_response_message_dict['content']}")
                    
                    # After processing all tool calls from this LLM response,
                    # loop back to call LLM again with the new tool results in history.
                    continue # Go to next iteration of the while loop to send tool results back to LLM

                else: # No tool calls, or not in COC mode with tools
                    if ai_content: # Normal text response
                        self.history_store.add_assistant_message(ai_content)
                        print(f"AI: {ai_content}")
                    elif not ai_tool_calls: # No content and no tool calls
                        print("System: AI did not provide a response or an error occurred.")
                    break # Exit the tool iteration loop, turn is over.
            
            if current_tool_iterations >= MAX_TOOL_ITERATIONS:
                print("System: Reached maximum tool iterations for this turn.")


if __name__ == "__main__":
    plugin = None
    if len(sys.argv) > 1:
        plugin_arg = sys.argv[1].strip().lower()
        if plugin_arg in ["coc", "haiguitang"]: # Add other plugins here
            plugin = plugin_arg
            print(f"Attempting to start in '{plugin}' plugin mode.")
        else:
            print(f"Warning: Unknown plugin mode '{plugin_arg}'. Starting in default mode.")

    app = ChatApplication(plugin_mode=plugin)
    app.run_chat()
```

**5. ContextBuilder and Summarizer Enhancements for COC:**

* **ContextBuilder (`get_and_manage_context`)**:

  * If in COC mode, it could fetch a "world state summary" from `COCPlugin` and inject it.

    ```python
    # In ContextBuilder.get_and_manage_context
    # ...
    if self.coc_plugin_instance: # Assuming you pass the coc_plugin instance to ContextBuilder
        world_state = self.coc_plugin_instance.get_coc_world_state_summary()
        if world_state:
            # Inject as a high-priority system or assistant message
            # e.g., final_llm_messages.insert(1, {"role": "system", "content": f"--- CURRENT STATE ---\n{world_state}\n--- END STATE ---"})
            # Adjust token counting accordingly.
            pass 
    ```

  * This would require `ContextBuilder` to be aware of the active plugin or have a way to get plugin-specific context.

* **Summarizer (`summarize_messages`)**:

  * When summarizing COC history, use the `get_coc_summary_instruction_hint()` from `COCPlugin` to guide the summarization LLM.

    ```python
    # In ContextBuilder, when calling summarizer:
    summary_instruction = DEFAULT_SUMMARY_INSTRUCTION
    if self.coc_plugin_instance:
        summary_instruction = self.coc_plugin_instance.get_coc_summary_instruction_hint()
    
    summary_tuple = self.summarizer.summarize_messages(messages_to_summarize, instruction=summary_instruction)
    ```

**Key Interaction Points for COC:**

1.  **Initialization:** When `ChatApplication` starts in "coc" mode, it instantiates `COCPlugin`.
2.  **System Prompt:** `ContextBuilder` uses `COC_KP_PROMPT` (possibly enhanced by `coc_plugin.get_kp_system_prompt()`).
3.  **Tool Definition:** Before calling `llm_client.get_chat_completion`, `ChatApplication` gets the list of tools from `coc_plugin.define_coc_tools()` and passes it to the LLM.
4.  **LLM Requests Tool:** `llm_client` returns `tool_calls`.
5.  **Tool Execution:** `ChatApplication` iterates through `tool_calls`, uses `coc_plugin` methods (like `roll_dice`) via `execute_tool_call` to get results.
6.  **Tool Results to History:** The `tool` role messages (containing results and `tool_call_id`) are added to `HistoryStore`.
7.  **Looping:** `ChatApplication` sends the updated history (now including tool results) back to the LLM until the LLM provides a final textual response without further tool calls for that turn.
8.  **Summarization:** `ContextBuilder` uses COC-specific hints for the `Summarizer` if in COC mode.
9.  **(Optional) World State Injection:** `ContextBuilder` could periodically inject a structured summary of game state from `COCPlugin` into the context.

**Important Considerations for COC:**

*   **Character Sheets:** The `COCPlugin` needs a robust way to manage character sheets (HP, SAN, skills, inventory). This might involve a simple dictionary, a JSON file, or even a database for persistence.
*   **State Management:** The `COCPlugin` is stateful. It holds the current game state.
*   **Error Handling in Tools:** Tool functions in `COCPlugin` should be robust and return clear error messages (as JSON strings) if something goes wrong, so the LLM can potentially understand and react.
*   **Prompt Engineering for KP:** The `COC_KP_PROMPT` is crucial. It needs to clearly define the AI's role, responsibilities, tone, and how it should use the provided tools. You might need to iterate on this prompt significantly.
*   **LLM Choice:** For complex tasks like being a KP and using tools effectively, more capable models (like GPT-4 or newer GPT-3.5 versions) will perform better.
*   **Token Limits with Tools:** The JSON for tool definitions, tool call requests, and tool responses all consume tokens. Efficient design of tool parameters and concise responses is important.

This detailed breakdown should give you a solid plan for integrating your COC跑团插件. It involves creating the plugin logic, modifying the LLM client to support tools, and updating the main application loop to handle the tool execution flow.

****