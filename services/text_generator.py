import groq
import os
import json
import re
from crewai import Agent, Crew, Process, Task
from services.story_agents.idea_crew_service import IdeaCrewService

class TextGenerator:
    def __init__(self):
        self.client = groq.Groq(api_key=os.environ.get('GROQ_API_KEY'))
        self.idea_crew = IdeaCrewService()
    
    def generate_story_concept(self, prompt, genre, mood, target_audience):
        try:
            # Create agents with proper configuration
            concept_generator = Agent(
                role=self.idea_crew.agents_config['concept_generator']['role'].format(topic=genre),
                goal=self.idea_crew.agents_config['concept_generator']['goal'].format(topic=genre),
                backstory=self.idea_crew.agents_config['concept_generator']['backstory'].format(topic=genre),
                verbose=True,
                llm_config={"temperature": 0.8}
            )
            
            world_builder = Agent(
                role=self.idea_crew.agents_config['world_builder']['role'].format(topic=genre),
                goal=self.idea_crew.agents_config['world_builder']['goal'].format(topic=genre),
                backstory=self.idea_crew.agents_config['world_builder']['backstory'].format(topic=genre),
                verbose=True,
                llm_config={"temperature": 0.7}
            )
            
            plot_weaver = Agent(
                role=self.idea_crew.agents_config['plot_weaver']['role'].format(topic=genre),
                goal=self.idea_crew.agents_config['plot_weaver']['goal'].format(topic=genre),
                backstory=self.idea_crew.agents_config['plot_weaver']['backstory'].format(topic=genre),
                verbose=True,
                llm_config={"temperature": 0.7}
            )

            # Create tasks with specific contexts
            generate_concepts_task = Task(
                description=self.idea_crew.tasks_config['generate_core_concepts']['description'],
                expected_output=self.idea_crew.tasks_config['generate_core_concepts']['expected_output'],
                agent=concept_generator,
                context=[
                    f"Generate a {genre} story concept with {mood} mood for {target_audience}.",
                    f"Story prompt: {prompt}",
                    "Provide a detailed response with clear sections for themes, narrative elements, and key story points."
                ]
            )

            develop_world_task = Task(
                description=self.idea_crew.tasks_config['develop_story_world']['description'],
                expected_output=self.idea_crew.tasks_config['develop_story_world']['expected_output'],
                agent=world_builder,
                context=[
                    "Based on the generated concept above, develop the story world.",
                    f"Consider the {genre} genre elements and {mood} atmosphere.",
                    "Detail the setting, environment, and world rules that support the story."
                ]
            )

            craft_plot_task = Task(
                description=self.idea_crew.tasks_config['craft_plot_possibilities']['description'],
                expected_output=self.tasks_config['craft_plot_possibilities']['expected_output'],
                agent=plot_weaver,
                context=[
                    "Using the established concept and world, outline the plot structure.",
                    f"Focus on creating a {mood} narrative that appeals to {target_audience}.",
                    "Include potential story arcs, conflicts, and character dynamics."
                ]
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute crew and process results
            results = crew.kickoff()
            if not results:
                raise Exception("No results returned from crew execution")

            return {
                'core_concepts': str(results[0]) if results[0] else "",
                'story_world': str(results[1]) if len(results) > 1 and results[1] else "",
                'plot_possibilities': str(results[2]) if len(results) > 2 and results[2] else ""
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None

    def generate_story(self, prompt, genre, mood, target_audience, paragraphs):
        try:
            # First, generate the story concept using the Idea Crew
            story_concept = self.generate_story_concept(prompt, genre, mood, target_audience)
            if not story_concept:
                raise Exception("Failed to generate story concept")

            # Use the story concept to generate the actual story text
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a creative storyteller specializing in {genre} stories with a {mood} mood for a {target_audience} audience. Write a story in a natural flowing narrative style."},
                    {"role": "user", "content": f'''
                        Using this story concept:
                        Core Concepts: {story_concept['core_concepts']}
                        Story World: {story_concept['story_world']}
                        Plot: {story_concept['plot_possibilities']}
                        
                        Write a {genre} story with a {mood} mood for a {target_audience} audience. 
                        Write it as {paragraphs} distinct paragraphs, where each paragraph naturally 
                        flows and contains approximately 2-3 sentences. Do not include any segment 
                        markers or labels.
                    '''}
                ],
                temperature=0.7,
            )
            
            if not response or not response.choices:
                raise Exception("No response from story generation API")
                
            story = response.choices[0].message.content
            if not story:
                raise Exception("Empty response from story generation API")
            
            # Split and clean paragraphs
            paragraphs_raw = story.split('\n\n')
            story_paragraphs = []
            
            for paragraph in paragraphs_raw:
                cleaned = re.sub(r'^[0-9]+[\.\)]\s*', '', paragraph.strip())
                cleaned = re.sub(r'Segment\s*[0-9]+:?\s*', '', cleaned)
                
                if cleaned:
                    story_paragraphs.append(cleaned)
                    
            return story_paragraphs[:paragraphs]
            
        except Exception as e:
            print(f"Error generating story: {str(e)}")
            return None
