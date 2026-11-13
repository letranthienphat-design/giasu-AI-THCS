# Lấy tất cả mô hình hội thoại khả dụng (bao gồm cả Gemini và Gemma 3)
                available_models = []
                for m in client.models.list():
                    name = m.name.replace("models/", "")
                    if ("gemini" in name or "gemma-3-27b" in name or "gemma-3-12b" in name) and not any(
                        x in name for x in ["embedding", "tts", "image", "audio", "pro", "exp"]
                    ):
                        available_models.append(name)
                
                available_models.sort(reverse=True)
                if not available_models:
                    available_models = ["gemini-2.5-flash", "gemma-3-27b-it"]

                response = None
                last_error = None

                for current_model in available_models[:4]:
                    try:
                        if "gemma" in current_model:
                            # Gemma gộp hướng dẫn hệ thống vào đầu câu hỏi
                            gemma_contents = [
                                types.Content(role="user", parts=[types.Part.from_text(text=f"Hướng dẫn vai trò:\n{system_instruction}\n\nCâu hỏi của học sinh: {prompt}")])
                            ]
                            response = client.models.generate_content(
                                model=current_model,
                                contents=gemma_contents,
                                config=types.GenerateContentConfig(temperature=0.4)
                            )
                        else:
                            contents = []
                            for m in st.session_state.messages[:-1]:
                                role_gemini = "user" if m["role"] == "user" else "model"
                                contents.append(types.Content(role=role_gemini, parts=[types.Part.from_text(text=m["content"])]))
                            current_parts = [types.Part.from_text(text=prompt)]
                            if image_data is not None:
                                current_parts.append(image_data)
                            contents.append(types.Content(role="user", parts=current_parts))

                            response = client.models.generate_content(
                                model=current_model,
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    temperature=0.4,
                                )
                            )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_error = err
                        time.sleep(1)
                        continue
