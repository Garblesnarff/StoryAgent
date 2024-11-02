from crewai import Agent, Crew, Process, Task
import yaml
import os
import json

class IdeaCrewService:
    def __init__(self):
        # Load agent and task configurations
        self.agents_config = self._load_config('config/agents.yaml')
        self.tasks_config = self._load_config('config/tasks.yaml')
        
    def _load_config(self, path):
        config_path = os.path.join(os.path.dirname(__file__), path)
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def create_agent(self, config):
        """Create an agent with the specified configuration"""
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=config.get('tools', []),
            allow_delegation=config.get('allow_delegation', False),
            verbose=config.get('verbose', True),
            llm_config=config.get('llm_config', {})
        )

    def create_task(self, config, agent, context=None):
        """Create a task with the specified configuration"""
        task_config = {
            'description': config['description'],
            'expected_output': config['expected_output'],
            'agent': agent
        }
        
        if context:
            task_config['context'] = [context]
            
        return Task(**task_config)

    def generate_story_concept(self, prompt, genre, mood, target_audience):
        """Generates a complete story concept using the Idea Crew"""
        try:
            # Create agents
            concept_generator = self.create_agent(self.agents_config['concept_generator'])
            world_builder = self.create_agent(self.agents_config['world_builder'])
            plot_weaver = self.create_agent(self.agents_config['plot_weaver'])

            # Create tasks with context and structured output format
            generate_concepts_task = self.create_task(
                self.tasks_config['generate_core_concepts'],
                concept_generator,
                context=f'''Create a story concept based on:
                        Prompt: {prompt}
                        Genre: {genre}
                        Mood: {mood}
                        Target Audience: {target_audience}
                        
                        Format your response with clear sections for:
                        - Main Theme
                        - Key Elements
                        - Potential Directions'''
            )

            develop_world_task = self.create_task(
                self.tasks_config['develop_story_world'],
                world_builder,
                context='''Based on the core concepts provided, develop a detailed world.
                        Structure your response with:
                        - Setting Description
                        - Key Locations
                        - Atmosphere
                        - Background Elements'''
            )

            craft_plot_task = self.create_task(
                self.tasks_config['craft_plot_possibilities'],
                plot_weaver,
                context='''Using the established world and concepts, outline the plot.
                        Include:
                        - Story Arcs
                        - Main Conflicts
                        - Character Dynamics'''
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Get results from crew execution and format them
            results = crew.kickoff()
            
            # Ensure we have all required results
            if len(results) < 3:
                raise Exception("Incomplete results from crew execution")

            # Format the results into a structured dictionary
            return {
                'core_concepts': str(results[0]).strip(),
                'story_world': str(results[1]).strip(),
                'plot_possibilities': str(results[2]).strip()
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
