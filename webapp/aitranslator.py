import os
from groq import Groq
from deep_translator import GoogleTranslator

class Textify:
    def __init__(self):
        self.groq_client = Groq(
            api_key="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"
        )

    def translate_text(self, text, target_lang='en', source_lang='auto'):
        """
        Translate text from source language to target language
        """
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            return translator.translate(text)
        except Exception as e:
            return f"Translation error: {str(e)}"

        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Improve the given translation while maintaining its original meaning."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return translated_text  # Return the basic translation if AI enhancement fails

# Example usage
if __name__ == "__main__":
    textify = Textify()
    
    print("Welcome to Textify! (Type 'quit' to exit)")

    
    while True:
        text = input("\nEnter text to translate: ")
        source_lang= input("enter source language: ")
        target_lang= input("enter target language:")
        if text.lower() == 'quit':
            break
            
        try:
            print("\nBasic Translation:")
            print(textify.translate_text(text, target_lang, source_lang))
            
        
            
        except ValueError:
            print("Please use the correct format: text | source_language | target_language")
        except Exception as e:
            print(f"An error occurred: {str(e)}")