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
            # Ensure context is a list
            task_config['context'] = [context] if isinstance(context, str) else context
            
        return Task(**task_config)

    def generate_story_concept(self, prompt, genre, mood, target_audience):
        """Generates a complete story concept using the Idea Crew"""
        try:
            # Create agents
            concept_generator = self.create_agent(self.agents_config['concept_generator'])
            world_builder = self.create_agent(self.agents_config['world_builder'])
            plot_weaver = self.create_agent(self.agents_config['plot_weaver'])

            # Create tasks with contexts as lists
            generate_concepts_task = self.create_task(
                self.tasks_config['generate_core_concepts'],
                concept_generator,
                [f"Generate a {genre} story concept with {mood} mood for {target_audience} based on: {prompt}"]
            )

            develop_world_task = self.create_task(
                self.tasks_config['develop_story_world'],
                world_builder,
                ["Use the above concept to develop the story world"]
            )

            craft_plot_task = self.create_task(
                self.tasks_config['craft_plot_possibilities'],
                plot_weaver,
                ["Create plot developments based on the world and concept above"]
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )

            results = crew.kickoff()
            
            if not results or len(results) < 3:
                raise Exception("Incomplete results from crew execution")

            return {
                'core_concepts': str(results[0]),
                'story_world': str(results[1]),
                'plot_possibilities': str(results[2])
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
