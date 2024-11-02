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

            # Create tasks with context
            generate_concepts_task = self.create_task(
                self.tasks_config['generate_core_concepts'],
                concept_generator,
                context=f"Create a story concept based on: Prompt: {prompt}, Genre: {genre}, Mood: {mood}, Target Audience: {target_audience}. Provide a structured response with main themes, key elements, and potential directions."
            )

            develop_world_task = self.create_task(
                self.tasks_config['develop_story_world'],
                world_builder,
                context="Based on the core concepts provided, develop a rich and detailed world for the story. Include key locations, atmosphere, and any relevant background elements."
            )

            craft_plot_task = self.create_task(
                self.tasks_config['craft_plot_possibilities'],
                plot_weaver,
                context="Using the established world and concepts, create potential plot developments. Include possible story arcs, conflicts, and character dynamics."
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Process and structure the results
            return {
                'core_concepts': result[0],
                'story_world': result[1],
                'plot_possibilities': result[2]
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
