import simpy
import random
import statistics
import pandas as pd
import os
import argparse


class GuitarManufacturer:
    def __init__(self, env, process_times, resources, num_guitars_ordered):
        self.env = env
        self.process_times = process_times
        self.resources = resources
        self.target_guitars = num_guitars_ordered
        self.completed_guitars = 0
        self.step_times = {}  # Dictionary to store step times per guitar
        self.cnc_machine = simpy.Resource(env, capacity=resources['cnc_machines'])
        self.cnc_operator = simpy.Resource(env, capacity=resources['cnc_operators'])
        self.neck_shaper = simpy.Resource(env, capacity=resources['neck_shaper'])
        self.assemblers = simpy.Resource(env, capacity=resources['assemblers'])
        self.setup_people = simpy.Resource(env, capacity=resources['setup_people'])
        self.plek_machine = simpy.Resource(env, capacity=resources['plek_machine'])

    def cut_body(self):
        with self.cnc_machine.request() as request:
            yield request
            with self.cnc_operator.request() as operator_request:
                yield operator_request
                start_time = self.env.now
                yield self.env.timeout(random.uniform(*self.process_times['cut_body']))
                end_time = self.env.now
                self.step_times.setdefault('cut_body', []).append(end_time - start_time)
                print("Body cut at", end_time)

    def route_cavities(self):
        with self.cnc_machine.request() as request:
            yield request
            with self.cnc_operator.request() as operator_request:
                yield operator_request
                start_time = self.env.now
                yield self.env.timeout(random.uniform(*self.process_times['route_cavities']))
                end_time = self.env.now
                self.step_times.setdefault('route_cavities', []).append(end_time - start_time)
                print("Cavities routed at", end_time)

    def rough_cut_neck(self):
        with self.cnc_machine.request() as request:
            yield request
            start_time = self.env.now
            yield self.env.timeout(random.uniform(*self.process_times['rough_cut_neck']))
            end_time = self.env.now
            self.step_times.setdefault('rough_cut_neck', []).append(end_time - start_time)
            print("Neck rough cut at", end_time)

    def shape_neck(self):
        with self.neck_shaper.request() as request:
            yield request
            start_time = self.env.now
            yield self.env.timeout(random.uniform(*self.process_times['shape_neck']))
            end_time = self.env.now
            self.step_times.setdefault('shape_neck', []).append(end_time - start_time)
            print("Neck shaped at", end_time)

    def assemble_guitar(self):
        with self.assemblers.request() as request:
            yield request
            start_time = self.env.now
            yield self.env.timeout(random.uniform(*self.process_times['assemble_guitar']))
            end_time = self.env.now
            self.step_times.setdefault('assemble_guitar', []).append(end_time - start_time)
            print("Guitar assembled at", end_time)
            self.completed_guitars += 1
            if self.completed_guitars >= self.target_guitars:
                self.env.exit()  # Exit the simulation

    def setup_guitar(self):
        with self.setup_people.request() as request:
            yield request
            start_time = self.env.now
            yield self.env.timeout(random.uniform(*self.process_times['setup_guitar']))
            end_time = self.env.now
            self.step_times.setdefault('setup_guitar', []).append(end_time - start_time)
            print("Guitar set up at", end_time)

    def run_plek_machine(self):
        with self.plek_machine.request() as request:
            yield request
            start_time = self.env.now
            yield self.env.timeout(random.uniform(*self.process_times['run_plek_machine']))
            end_time = self.env.now
            self.step_times.setdefault('run_plek_machine', []).append(end_time - start_time)
            print("Guitar run through Plek machine at", end_time)

    def run(self):
        yield self.env.process(self.cut_body())
        yield self.env.process(self.route_cavities())
        yield self.env.process(self.rough_cut_neck())
        yield self.env.process(self.shape_neck())
        yield self.env.process(self.assemble_guitar())
        yield self.env.process(self.setup_guitar())
        yield self.env.process(self.run_plek_machine())


def simulate_guitar_production(target_guitars, resources, num_simulations):
    env = simpy.Environment()
    process_times = {
        'cut_body': (25, 35),
        'route_cavities': (10, 20),
        'rough_cut_neck': (15, 25),
        'shape_neck': (360, 390),
        'assemble_guitar': (240, 250),
        'setup_guitar': (180, 190),
        'run_plek_machine': (120, 122)
    }

    scaling_factor = target_guitars / 10  # Adjust based on the desired target_guitars
    scaled_resources = {resource: int(capacity * scaling_factor) for resource, capacity in resources.items()}
    scaled_process_times = {step: (min_time * scaling_factor, max_time * scaling_factor)
                            for step, (min_time, max_time) in process_times.items()}

    total_times = []
    for _ in range(num_simulations):
        env = simpy.Environment()
        manufacturer = GuitarManufacturer(env, scaled_process_times, scaled_resources, target_guitars)
        env.process(manufacturer.run())
        env.run()
        total_times.append(sum(sum(step_times) for step_times in manufacturer.step_times.values()))

    average_time_required = statistics.mean(total_times)
    return average_time_required, total_times


if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='Simulate guitar production.')

    # Add command line arguments
    parser.add_argument('--simulations', type=int, default=1000, help='number of simulations to run')
    parser.add_argument('--guitars', type=int, default=100, help='number of guitars per simulation')

    # Parse the command line arguments
    args = parser.parse_args()

    # Extract the values from the parsed arguments
    num_simulations = args.simulations
    target_guitars = args.guitars

    resources = {
        'cnc_machines': 2,
        'cnc_operators': 2,
        'neck_shaper': 1,
        'assemblers': 2,
        'setup_people': 2,
        'plek_machine': 1
    }

    average_time_required, total_times = simulate_guitar_production(target_guitars, resources, num_simulations)

    print("Number of simulations:", num_simulations)
    print("Number of guitars per simulation:", target_guitars)
    print("Average time required to complete orders:", average_time_required, "minutes")

    # Create a Pandas DataFrame
    data = {'Simulation': range(1, num_simulations + 1), 'Total Time (minutes)': total_times}
    df = pd.DataFrame(data)

    # Create the outputs folder if it doesn't exist
    if not os.path.exists('output'):
        os.makedirs('output')

    # Save the DataFrame as a CSV file in the outputs folder
    output_file = 'output/guitar_production_times.csv'
    df.to_csv(output_file, index=False)
    print("Guitar production times saved to", output_file)