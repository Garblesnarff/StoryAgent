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
        try:
            # Create agents with proper format strings in their configs
            concept_generator = self.create_agent({
                **self.agents_config['concept_generator'],
                'role': self.agents_config['concept_generator']['role'].format(topic=genre)
            })
            world_builder = self.create_agent({
                **self.agents_config['world_builder'],
                'role': self.agents_config['world_builder']['role'].format(topic=genre)
            })
            plot_weaver = self.create_agent({
                **self.agents_config['plot_weaver'],
                'role': self.agents_config['plot_weaver']['role'].format(topic=genre)
            })

            # Create tasks with detailed contexts
            concept_context = [
                f"Generate a {genre} story concept with {mood} mood for {target_audience}.",
                f"Story prompt: {prompt}",
                "Provide a detailed response with clear sections for themes, narrative elements, and key story points."
            ]
            
            # Create sequential tasks
            generate_concepts_task = self.create_task(
                self.tasks_config['generate_core_concepts'],
                concept_generator,
                concept_context
            )

            world_context = [
                "Based on the generated concept above, develop the story world.",
                f"Consider the {genre} genre elements and {mood} atmosphere.",
                "Detail the setting, environment, and world rules that support the story."
            ]
            
            develop_world_task = self.create_task(
                self.tasks_config['develop_story_world'],
                world_builder,
                world_context
            )

            plot_context = [
                "Using the established concept and world, outline the plot structure.",
                f"Focus on creating a {mood} narrative that appeals to {target_audience}.",
                "Include potential story arcs, conflicts, and character dynamics."
            ]
            
            craft_plot_task = self.create_task(
                self.tasks_config['craft_plot_possibilities'],
                plot_weaver,
                plot_context
            )

            # Create and run the crew
            crew = Crew(
                agents=[concept_generator, world_builder, plot_weaver],
                tasks=[generate_concepts_task, develop_world_task, craft_plot_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute crew and get results
            results = crew.kickoff()
            
            if not results:
                raise Exception("No results returned from crew execution")

            # Extract results and ensure they are strings
            core_concepts = str(results[0]) if results[0] else ""
            story_world = str(results[1]) if len(results) > 1 and results[1] else ""
            plot_possibilities = str(results[2]) if len(results) > 2 and results[2] else ""

            return {
                'core_concepts': core_concepts,
                'story_world': story_world,
                'plot_possibilities': plot_possibilities
            }

        except Exception as e:
            print(f"Error in story concept generation: {str(e)}")
            return None
